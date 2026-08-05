#!/usr/bin/env python3
"""Check JSON Structure relations that the schema validators do not reach.

The JSON Structure SDK checks a relation declaration in isolation: that
``identity`` names real properties, that ``targettype`` resolves, that
``cardinality`` is one of the two permitted values, and that ``scope`` is a
pointer or an array of pointers. Every remaining rule in the Relations
specification is about how one node relates to another, and no single-node
check can express it.

This script closes that gap. On the schema it verifies that a relation name
does not collide with a property name of the same type, that every target type
carries an identity declaration, that every scope resolves to a collection of
the target type, and that a qualifier type is an object type. On an instance it
verifies that each relation member has the shape its cardinality calls for,
that identity values are given in the order the target declares them, that a
qualifier appears only where a qualifier type was declared, and that every
identity resolves to an object inside one of the declared scopes.

Usage:
    python check-relations.py <schema> [<instance>]
"""

import json
import sys

COLLECTIONS = ("array", "set", "map")


class SchemaError(Exception):
    """A schema is malformed in a way that stops the checks from running."""


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def escape(token):
    return token.replace("~", "~0").replace("/", "~1")


class Schema:
    """A schema document with the pointer and inheritance handling the checks need."""

    def __init__(self, doc):
        self.doc = doc

    def resolve(self, pointer):
        if not isinstance(pointer, str) or not pointer.startswith("#"):
            raise SchemaError("not a document-local JSON pointer: %r" % (pointer,))
        node = self.doc
        for token in pointer[1:].split("/")[1:]:
            token = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or token not in node:
                raise SchemaError("pointer does not resolve: " + pointer)
            node = node[token]
        if not isinstance(node, dict):
            raise SchemaError("pointer does not name a schema node: " + pointer)
        return node

    def kind(self, node):
        """Follow type references and return the type name with the node that carries it."""
        seen = set()
        while True:
            declared = node.get("type")
            if isinstance(declared, dict) and "$ref" in declared:
                if id(node) in seen:
                    raise SchemaError("type reference cycle at " + declared["$ref"])
                seen.add(id(node))
                node = self.resolve(declared["$ref"])
                continue
            return (declared if isinstance(declared, str) else None), node

    def members(self, node):
        """Return properties, identity, relations and tuple order with $extends applied."""
        chain = []
        current = node
        while isinstance(current, dict):
            chain.append(current)
            base = current.get("$extends")
            current = self.resolve(base) if isinstance(base, str) else None
        properties, relations = {}, {}
        identity, order = None, None
        for current in reversed(chain):
            properties.update(current.get("properties", {}))
            relations.update(current.get("relations", {}))
            if "identity" in current:
                identity = current["identity"]
            if "tuple" in current:
                order = current["tuple"]
        return properties, identity, relations, order

    def scope_node(self, scope):
        """Resolve a scope pointer, treating '#' as the root type."""
        if scope == "#":
            root = self.doc.get("$root")
            if not isinstance(root, str):
                raise SchemaError("scope '#' requires a $root declaration")
            return self.resolve(root)
        return self.resolve(scope)


def iter_nodes(node, pointer="#"):
    """Yield every dictionary in the document with its JSON pointer."""
    if isinstance(node, dict):
        yield pointer, node
        for key, value in node.items():
            yield from iter_nodes(value, pointer + "/" + escape(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_nodes(value, pointer + "/" + str(index))


def scopes_of(declaration):
    scope = declaration.get("scope")
    if scope is None:
        return []
    if isinstance(scope, str):
        return [scope]
    return list(scope)


def identity_of(schema, target):
    """Return the identity property names declared by a target type."""
    _, node = schema.kind(target)
    _, identity, _, _ = schema.members(node)
    return identity


def identity_values(schema, target, element):
    """Read the identity of an instance element, positionally for tuple types."""
    kind, node = schema.kind(target)
    properties, identity, _, order = schema.members(node)
    if not identity:
        return None
    if kind == "tuple":
        if not isinstance(element, list):
            return None
        positions = {name: index for index, name in enumerate(order or [])}
        values = []
        for name in identity:
            index = positions.get(name)
            if index is None or index >= len(element):
                return None
            values.append(element[index])
        return tuple(values)
    if not isinstance(element, dict):
        return None
    return tuple(element.get(name) for name in identity)


def stated_identity(identity, value):
    """Read the identity carried by a relation instance, or None if malformed."""
    if len(identity) == 1:
        if isinstance(value, list):
            return tuple(value) if len(value) == 1 else None
        return (value,)
    if isinstance(value, list) and len(value) == len(identity):
        return tuple(value)
    return None


def hashable(key):
    return all(isinstance(value, (str, int, float, bool)) or value is None for value in key)


def check_schema(schema, errors):
    for pointer, node in iter_nodes(schema.doc):
        relations = node.get("relations")
        if not isinstance(relations, dict):
            continue
        properties, _, _, _ = schema.members(node)
        for name, declaration in relations.items():
            where = "%s/relations/%s" % (pointer, name)
            if not isinstance(declaration, dict):
                continue
            if name in properties:
                errors.append(
                    "%s: relation name collides with a property of the same type; "
                    "relations and properties share one namespace in an instance" % where
                )
            check_target(schema, declaration, where, errors)
            check_qualifier(schema, declaration, where, errors)
            check_scopes(schema, declaration, where, errors)


def check_target(schema, declaration, where, errors):
    reference = declaration.get("targettype")
    if not isinstance(reference, dict) or "$ref" not in reference:
        return
    try:
        target = schema.resolve(reference["$ref"])
    except SchemaError as failure:
        errors.append("%s/targettype: %s" % (where, failure))
        return
    if not identity_of(schema, target):
        errors.append(
            "%s/targettype: target type %s declares no identity, so nothing can "
            "reference it" % (where, reference["$ref"])
        )


def check_qualifier(schema, declaration, where, errors):
    reference = declaration.get("qualifiertype")
    if reference is None:
        return
    if not isinstance(reference, dict) or "$ref" not in reference:
        return
    try:
        kind, _ = schema.kind(schema.resolve(reference["$ref"]))
    except SchemaError as failure:
        errors.append("%s/qualifiertype: %s" % (where, failure))
        return
    if kind != "object":
        errors.append(
            "%s/qualifiertype: qualifier type is %s, but a qualifier is a set of "
            "named values and must be an object type" % (where, kind)
        )


def check_scopes(schema, declaration, where, errors):
    reference = declaration.get("targettype")
    if not isinstance(reference, dict) or "$ref" not in reference:
        return
    try:
        target = schema.resolve(reference["$ref"])
        _, target_node = schema.kind(target)
    except SchemaError:
        return
    for scope in scopes_of(declaration):
        try:
            kind, node = schema.kind(schema.scope_node(scope))
        except SchemaError as failure:
            errors.append("%s/scope: %s" % (where, failure))
            continue
        if kind not in COLLECTIONS:
            errors.append(
                "%s/scope: '%s' names a %s, but a scope must name an array, a set "
                "or a map to be searched" % (where, scope, kind)
            )
            continue
        element = node.get("items") if kind in ("array", "set") else node.get("values")
        if not isinstance(element, dict):
            continue
        try:
            _, element_node = schema.kind(element)
        except SchemaError as failure:
            errors.append("%s/scope: %s" % (where, failure))
            continue
        if element_node is not target_node:
            errors.append(
                "%s/scope: '%s' holds a different type from the relation target %s"
                % (where, scope, reference["$ref"])
            )


class Walk:
    """Instance elements gathered per collection, and the relations found on the way."""

    def __init__(self):
        self.collections = {}
        self.relations = []

    def collect(self, node, elements):
        self.collections.setdefault(id(node), []).extend(elements)


def walk(schema, node, instance, pointer, state):
    kind, definition = schema.kind(node)
    if kind in ("array", "set"):
        if not isinstance(instance, list):
            return
        state.collect(definition, instance)
        element = definition.get("items")
        if isinstance(element, dict):
            for index, value in enumerate(instance):
                walk(schema, element, value, "%s/%d" % (pointer, index), state)
    elif kind == "map":
        if not isinstance(instance, dict):
            return
        state.collect(definition, list(instance.values()))
        element = definition.get("values")
        if isinstance(element, dict):
            for key, value in instance.items():
                walk(schema, element, value, pointer + "/" + escape(key), state)
    elif kind == "object":
        if not isinstance(instance, dict):
            return
        properties, _, relations, _ = schema.members(definition)
        for name, declaration in relations.items():
            if name in instance and isinstance(declaration, dict):
                state.relations.append(
                    (pointer + "/" + escape(name), name, declaration, instance[name])
                )
        for name, property_node in properties.items():
            if name in instance and isinstance(property_node, dict):
                walk(schema, property_node, instance[name], pointer + "/" + escape(name), state)
    elif kind == "tuple":
        if not isinstance(instance, list):
            return
        properties, _, _, order = schema.members(definition)
        for index, name in enumerate(order or []):
            if index < len(instance) and isinstance(properties.get(name), dict):
                walk(schema, properties[name], instance[index], "%s/%d" % (pointer, index), state)


def build_index(schema, state, declaration, target):
    """Index every element in scope by its identity."""
    index = {}
    for scope in scopes_of(declaration):
        try:
            _, node = schema.kind(schema.scope_node(scope))
        except SchemaError:
            continue
        for element in state.collections.get(id(node), []):
            key = identity_values(schema, target, element)
            if key is not None and hashable(key):
                index.setdefault(key, []).append(element)
    return index


def check_instance(schema, instance, errors):
    root = schema.doc.get("$root")
    if not isinstance(root, str):
        errors.append("#: the schema declares no $root, so the instance cannot be walked")
        return
    state = Walk()
    walk(schema, schema.resolve(root), instance, "#", state)
    for pointer, name, declaration, value in state.relations:
        check_relation_instance(schema, state, pointer, declaration, value, errors)


def check_relation_instance(schema, state, pointer, declaration, value, errors):
    reference = declaration.get("targettype")
    if not isinstance(reference, dict) or "$ref" not in reference:
        return
    try:
        target = schema.resolve(reference["$ref"])
    except SchemaError:
        return
    identity = identity_of(schema, target)
    if not identity:
        return
    cardinality = declaration.get("cardinality")
    if cardinality == "single":
        if not isinstance(value, dict):
            errors.append(
                "%s: cardinality is 'single', so the relation is one object, not %s"
                % (pointer, json_kind(value))
            )
            return
        entries = [(pointer, value)]
    else:
        if not isinstance(value, list):
            errors.append(
                "%s: cardinality is 'multiple', so the relation is an array, not %s"
                % (pointer, json_kind(value))
            )
            return
        entries = [("%s/%d" % (pointer, index), entry) for index, entry in enumerate(value)]

    index = None
    for where, entry in entries:
        if not isinstance(entry, dict):
            errors.append("%s: a relation instance is an object, not %s" % (where, json_kind(entry)))
            continue
        if "identity" not in entry:
            errors.append("%s: relation instance has no 'identity' member" % where)
            continue
        if "qualifier" in entry and "qualifiertype" not in declaration:
            errors.append(
                "%s: relation instance carries a 'qualifier', but the declaration "
                "names no qualifier type" % where
            )
        key = stated_identity(identity, entry["identity"])
        if key is None:
            errors.append(
                "%s/identity: target identity is %s, so the value is an array of %d "
                "values in that order" % (where, ", ".join(identity), len(identity))
            )
            continue
        if not scopes_of(declaration):
            continue
        if index is None:
            index = build_index(schema, state, declaration, target)
        if not hashable(key):
            continue
        if key not in index:
            errors.append(
                "%s/identity: no object in scope has identity %s"
                % (where, " / ".join(repr(value) for value in key))
            )
        elif len(index[key]) > 1:
            errors.append(
                "%s/identity: identity %s is not unique in scope; %d objects carry it"
                % (where, " / ".join(repr(value) for value in key), len(index[key]))
            )


def json_kind(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "a boolean"
    if isinstance(value, (int, float)):
        return "a number"
    if isinstance(value, str):
        return "a string"
    if isinstance(value, list):
        return "an array"
    return "an object"


def main(argv):
    if not 1 <= len(argv) <= 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    schema = Schema(load(argv[0]))
    errors = []
    try:
        check_schema(schema, errors)
        if len(argv) == 2:
            check_instance(schema, load(argv[1]), errors)
    except SchemaError as failure:
        errors.append(str(failure))
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
