---
title: "JSON Structure: Relations"
category: std

docname: draft-vasters-json-structure-relations-latest
submissiontype: IETF  # also: "independent", "editorial", "IAB", or "IRTF"
number:
date: 2025-11-28
consensus: true
v: 3
area: "Applications"
workgroup: "JavaScript Object Notation"
keyword: Internet-Draft
venue:
  group: "JavaScript Object Notation"
  type: "Working Group"
  mail: "json@ietf.org"
  arch: "https://mailarchive.ietf.org/arch/browse/json"
  github: "json-structure/relations"
  latest: "https://json-structure.github.io/relations/draft-vasters-json-structure-relations.html"

author:
 -
    fullname: Clemens Vasters
    organization: Microsoft Corporation
    email: clemensv@microsoft.com

normative:
  RFC6901:
  RFC8259:
  RFC9562:
  JSTRUCT-CORE:
    title: "JSON Structure Core"
    author:
      - fullname: Clemens Vasters
    target: https://json-structure.github.io/core/draft-vasters-json-structure-core.html

informative:


--- abstract

This document is an extension to JSON Structure Core. It defines keywords for
modeling relationships and associations between objects in JSON Structure
schemas, including the `identity`, `relations`, `targettype`, `cardinality`,
`scope`, and `qualifiertype` keywords.

--- middle

# Introduction {#introduction}

This document is an extension to JSON Structure Core {{JSTRUCT-CORE}}. It
defines keywords for modeling relationships and associations between objects in
JSON Structure schemas.

In many data models, objects need to reference other objects to express
relationships such as authorship, ownership, membership, or other associations.
This specification provides a structured way to declare such relationships
within JSON Structure schemas.

The key concepts introduced are:

- **Identity**: A mechanism for uniquely identifying object instances based on
  one or more property values.
- **Relations**: Declarations that specify how one object type relates to
  another, including cardinality and optional qualifiers.

# Conventions {#conventions}

{::boilerplate bcp14-tagged}

# Identity {#identity}

The `identity` keyword is used to declare which properties of an object or tuple
uniquely identify instances of that type. The identity declaration functions
similarly to a primary key in relational databases.

## The `identity` Keyword {#identity-keyword}

The `identity` keyword MUST be used only with schemas of type `object` or
`tuple`. Its value MUST be an array of strings, where each string is the name of
a property defined in the `properties` map of the type.

When an object type has an `identity` declaration, any instance of that type MUST
be uniquely identified by the combination of its identity property values. Two
instances with the same identity values MUST NOT exist within the same identity
scope.

An identity scope is the boundary within which identity values must be unique.
Identity scopes MAY be:

- A collection within a document, such as an `array`, `set`, or `map` containing
  instances of the type.
- An entire document when instances are distributed across multiple collections.
- An external data source, such as a database or service, when the `identity`
  property is used to reference instances that exist outside the current
  document.

The specific identity scope is determined by the `scope` keyword in the relation
declaration. When `scope` is present, it identifies where in the document
instances of the target type can be found. When `scope` is absent, the identity
scope extends beyond the document to external data sources.

Example:

~~~ json
{
  "Author": {
    "type": "object",
    "properties": {
      "id": { "type": "uuid" },
      "name": { "type": "string" }
    },
    "required": ["id", "name"],
    "identity": ["id"]
  }
}
~~~

For objects with composite identities, multiple properties can be specified:

~~~ json
{
  "BookEdition": {
    "type": "object",
    "properties": {
      "isbn": { "type": "string" },
      "edition": { "type": "int32" },
      "title": { "type": "string" }
    },
    "required": ["isbn", "edition", "title"],
    "identity": ["isbn", "edition"]
  }
}
~~~

# Relations {#relations}

The `relations` keyword is used to declare relationship properties on object and
tuple types. Relations express associations between instances of different
types.

## The `relations` Keyword {#relations-keyword}

The `relations` keyword MUST only be used with schemas of type `object` or
`tuple`. Its value MUST be a JSON object where each key is a relation name and
each value is a relation declaration.

Relation names MUST conform to the same identifier rules as property names in
JSON Structure Core. The `relations` and `properties` keywords share a
namespace, meaning a relation name MUST NOT conflict with any property name in
the same type.

A relation declaration is a JSON object that defines the characteristics of the
relationship. It MUST contain the following properties:

- `targettype`: Declares the target type that the relation refers to.
- `cardinality`: Declares whether the relationship points to one or more targets
  (`single` or `multiple`).

A relation declaration MAY contain:

- `scope`: Specifies where instances of the target type can be found within the
  document.
- `qualifiertype`: Defines a type to qualify the relationship with additional
  properties (similar to link properties in graph models).

Example:

~~~ json
{
  "definitions": {
    "Author": {
      "type": "object",
      "properties": {
        "id": { "type": "uuid" },
        "name": { "type": "string" }
      },
      "required": ["id", "name"],
      "identity": ["id"]
    },
    "Book": {
      "type": "object",
      "properties": {
        "isbn": { "type": "string" },
        "title": { "type": "string" }
      },
      "required": ["isbn", "title"],
      "identity": ["isbn"],
      "relations": {
        "authors": {
          "cardinality": "multiple",
          "targettype": { "$ref": "#/definitions/Author" }
        }
      }
    }
  }
}
~~~

## The `targettype` Keyword {#targettype-keyword}

The `targettype` keyword specifies the target type of a relation. Its value MUST
be a schema containing a `$ref` keyword that points to a type definition with an
`identity` declaration.

The target type MUST have an `identity` declaration. This identity is used to
establish references between instances.

Example:

~~~ json
{
  "targettype": { "$ref": "#/definitions/Author" }
}
~~~

## The `cardinality` Keyword {#cardinality-keyword}

The `cardinality` keyword specifies whether a relation points to a single target
or multiple targets. Its value MUST be one of the following strings:

- `"single"`: The relation refers to exactly one target instance.
- `"multiple"`: The relation refers to zero or more target instances.

Example for a single-cardinality relation:

~~~ json
{
  "publisher": {
    "cardinality": "single",
    "targettype": { "$ref": "#/definitions/Publisher" }
  }
}
~~~

Example for a multiple-cardinality relation:

~~~ json
{
  "authors": {
    "cardinality": "multiple",
    "targettype": { "$ref": "#/definitions/Author" }
  }
}
~~~

## The `scope` Keyword {#scope-keyword}

The `scope` keyword specifies where instances of the target type can be found
within an instance document. When present, it indicates that the relation
references objects contained in the current document. When absent, the relation
references objects that exist in an external context, such as a database,
service, or another document.

The value of `scope` MUST be either:

- A string containing a JSON Pointer ({{RFC6901}}) to a schema location, or
- An array of strings, each containing a JSON Pointer to a schema location.

Each JSON Pointer MUST reference a valid location within the same schema
document. The referenced location MUST be one of the following:

- A property definition within a type whose value is an `array`, `set`, or
  `map` containing items compatible with `targettype`. For example:
  `#/definitions/Library/properties/authors`.

- The document root type (as declared by `$root`) if the root type is an
  `array`, `set`, or `map` containing items compatible with `targettype`. In
  this case, the scope value is `#` (pointing to the root).

The referenced type is considered compatible with `targettype` if the `items`
type (for `array` or `set`) or `values` type (for `map`) matches `targettype`
or is a subtype of `targettype`.

When resolving a relation at runtime, the application uses the `scope` to
identify which collections in the document instance contain potential target
objects. The application then searches these collections for an object whose
identity matches the `identity` value in the relation instance. For `map`
types, the application searches the map's values, not its keys.

Example with a single scope pointing to a property:

~~~ json
{
  "definitions": {
    "Library": {
      "type": "object",
      "properties": {
        "authors": {
          "type": "array",
          "items": { "$ref": "#/definitions/Author" }
        },
        "books": {
          "type": "array",
          "items": { "$ref": "#/definitions/Book" }
        }
      }
    },
    "Author": {
      "type": "object",
      "properties": {
        "id": { "type": "uuid" },
        "name": { "type": "string" }
      },
      "identity": ["id"]
    },
    "Book": {
      "type": "object",
      "properties": {
        "isbn": { "type": "string" },
        "title": { "type": "string" }
      },
      "identity": ["isbn"],
      "relations": {
        "authors": {
          "cardinality": "multiple",
          "targettype": { "$ref": "#/definitions/Author" },
          "scope": "#/definitions/Library/properties/authors"
        }
      }
    }
  }
}
~~~

Example with multiple scopes:

~~~ json
{
  "relations": {
    "contributors": {
      "cardinality": "multiple",
      "targettype": { "$ref": "#/definitions/Person" },
      "scope": [
        "#/definitions/Project/properties/teamMembers",
        "#/definitions/Project/properties/externalContributors"
      ]
    }
  }
}
~~~

Example of an external relation (no scope):

~~~ json
{
  "relations": {
    "customer": {
      "cardinality": "single",
      "targettype": { "$ref": "#/definitions/Customer" }
    }
  }
}
~~~

In this example, the absence of `scope` indicates that `Customer` instances are
not expected to be found in the document. The application must resolve the
reference through external means.

## The `qualifiertype` Keyword {#qualifiertype-keyword}

The `qualifiertype` keyword allows a relation to carry additional properties
that qualify the relationship itself, similar to link properties in graph
databases.

The value of `qualifiertype` MUST be a reference to a reusable type using the
`$ref` keyword.

Example:

~~~ json
{
  "definitions": {
    "Person": {
      "type": "object",
      "properties": {
        "id": { "type": "uuid" },
        "name": { "type": "string" }
      },
      "required": ["id", "name"],
      "identity": ["id"]
    },
    "ContributorQualifier": {
      "type": "object",
      "properties": {
        "role": { "type": "string" },
        "startDate": { "type": "date" },
        "endDate": { "type": "date" }
      },
      "required": ["role"]
    },
    "Project": {
      "type": "object",
      "properties": {
        "projectId": { "type": "string" },
        "name": { "type": "string" }
      },
      "required": ["projectId", "name"],
      "identity": ["projectId"],
      "relations": {
        "contributors": {
          "cardinality": "multiple",
          "targettype": { "$ref": "#/definitions/Person" },
          "qualifiertype": { "$ref": "#/definitions/ContributorQualifier" }
        }
      }
    }
  }
}
~~~

# Relation Instance Structure {#relation-instance-structure}

In JSON document instances, relations are represented as properties of the
containing object. The structure of a relation instance depends on its
cardinality.

## Single-Cardinality Relations {#single-cardinality-relations}

A single-cardinality relation is represented as a JSON object with the following
properties:

- `identity`: A value or tuple of values that match the identity of the target
  object.

If the relation has a `qualifiertype`, the qualifier properties are included
in a `qualifier` property within the relation object.

Example:

~~~ json
{
  "isbn": "978-0-123456-78-9",
  "title": "Example Book",
  "publisher": {
    "identity": "550e8400-e29b-41d4-a716-446655440000"
  }
}
~~~

With qualifier properties:

~~~ json
{
  "isbn": "978-0-123456-78-9",
  "title": "Example Book",
  "editor": {
    "identity": "650e8400-e29b-41d4-a716-446655440001",
    "qualifier": {
      "role": "Chief Editor",
      "startDate": "2020-01-15"
    }
  }
}
~~~

## Multiple-Cardinality Relations {#multiple-cardinality-relations}

A multiple-cardinality relation is represented as a JSON array. Each element of
the array is a relation object with the same structure as a single-cardinality
relation.

Example:

~~~ json
{
  "isbn": "978-0-123456-78-9",
  "title": "Example Book",
  "authors": [
    { "identity": "123e4567-e89b-12d3-a456-426614174000" },
    { "identity": "223e4567-e89b-12d3-a456-426614174001" }
  ]
}
~~~

With qualifier properties:

~~~ json
{
  "projectId": "proj-123",
  "name": "Example Project",
  "contributors": [
    {
      "identity": "323e4567-e89b-12d3-a456-426614174002",
      "qualifier": {
        "role": "Developer",
        "startDate": "2020-06-01"
      }
    },
    {
      "identity": "423e4567-e89b-12d3-a456-426614174003",
      "qualifier": {
        "role": "Designer",
        "startDate": "2020-06-15",
        "endDate": "2021-12-31"
      }
    }
  ]
}
~~~

## Identity Values {#identity-values}

The `identity` property in a relation object contains the identity value(s) of
the target object.

- If the target type's `identity` declaration specifies a single property, the
  `identity` value is a scalar matching that property's type.
- If the target type's `identity` declaration specifies multiple properties
  (composite identity), the `identity` value is a JSON array containing the
  values in the same order as declared in the `identity` keyword.

Example with single-property identity:

~~~ json
{
  "identity": "550e8400-e29b-41d4-a716-446655440000"
}
~~~

Example with composite identity:

~~~ json
{
  "identity": ["978-0-123456-78-9", 2]
}
~~~

## Reference Resolution {#reference-resolution}

A relationship is established through the `identity` property in a relation
instance, which contains the identity value(s) of the target object.

The resolution mechanism depends on whether the relation declaration includes a
`scope`:

- **With `scope`**: The application uses the schema pointers in `scope` to
  identify the corresponding collections in the document instance. It searches
  these collections for an object whose identity matches the `identity` value.
  For `map` collections, the search is performed on the map's values.

- **Without `scope`**: The relation references an object that exists outside
  the document. The application must resolve the reference through external
  means, such as querying a database or service.

# Complete Example {#complete-example}

This example demonstrates a library schema with books and authors:

~~~ json
{
  "$schema": "https://json-structure.org/meta/core/v0/#",
  "$id": "https://example.com/library",
  "$root": "#/definitions/Library",
  "definitions": {
    "Library": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "authors": {
          "type": "array",
          "items": { "$ref": "#/definitions/Author" }
        },
        "books": {
          "type": "array",
          "items": { "$ref": "#/definitions/Book" }
        }
      },
      "required": ["name", "authors", "books"]
    },
    "Author": {
      "type": "object",
      "properties": {
        "id": { "type": "uuid" },
        "name": { "type": "string" }
      },
      "required": ["id", "name"],
      "identity": ["id"]
    },
    "Book": {
      "type": "object",
      "properties": {
        "isbn": { "type": "string" },
        "title": { "type": "string" }
      },
      "required": ["isbn", "title"],
      "identity": ["isbn"],
      "relations": {
        "authors": {
          "cardinality": "multiple",
          "targettype": { "$ref": "#/definitions/Author" },
          "scope": "#/definitions/Library/properties/authors"
        }
      }
    }
  }
}
~~~

Example instance document:

~~~ json
{
  "$schema": "https://example.com/library",
  "name": "City Central Library",
  "authors": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Alice Smith"
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "name": "Bob Jones"
    }
  ],
  "books": [
    {
      "isbn": "978-0-123456-78-9",
      "title": "The Great Novel",
      "authors": [
        { "identity": "123e4567-e89b-12d3-a456-426614174000" }
      ]
    },
    {
      "isbn": "978-0-987654-32-1",
      "title": "Another Great Book",
      "authors": [
        { "identity": "123e4567-e89b-12d3-a456-426614174000" },
        { "identity": "223e4567-e89b-12d3-a456-426614174001" }
      ]
    }
  ]
}
~~~

# Reserved Keywords {#reserved-keywords}

This specification adds the following keywords to the JSON Structure reserved
keyword list:

- `identity`
- `relations`
- `targettype`
- `cardinality`
- `scope`
- `qualifiertype`

# Security Considerations {#security-considerations}

Relations create references between objects that may span different parts of a
document or different documents. Implementations MUST ensure that:

- Identity values are validated against the expected target type.
- Circular references are handled appropriately to prevent infinite loops during
  traversal.
- Identity matching across documents does not expose sensitive information
  through unintended correlations.

# IANA Considerations {#iana-considerations}

This document has no IANA actions.

--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
