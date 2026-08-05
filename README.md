<!-- regenerate: off (set to off if you edit this file) -->

# JSON Structure: Relations

This is the working area for the individual Internet-Draft, "JSON Structure: Relations".

* [Editor's Copy](https://json-structure.github.io/relations/#go.draft-vasters-json-structure-relations.html)
* [Datatracker Page](https://datatracker.ietf.org/doc/draft-vasters-json-structure-relations)
* [Individual Draft](https://datatracker.ietf.org/doc/html/draft-vasters-json-structure-relations)
* [Compare Editor's Copy to Individual Draft](https://json-structure.github.io/relations/#go.draft-vasters-json-structure-relations.diff)


## Contributing

See the
[guidelines for contributions](https://github.com/json-structure/relations/blob/main/CONTRIBUTING.md).

The contributing file also has tips on how to make contributions, if you
don't already know how to do that.

## Samples

Fourteen worked examples live in
[`samples/relations/`](https://github.com/json-structure/primer-and-samples/tree/main/samples/relations)
in the [primer-and-samples](https://github.com/json-structure/primer-and-samples)
repository. Each directory contains a `schema.struct.json` that declares the
extension meta-schema [`relations-v0.json`](relations-v0.json) and an
`example.json` instance that conforms to it.

Twelve teaching samples introduce the keywords one at a time: single and
composite identity, identity on a tuple type, both cardinalities, qualified
relations, scopes over arrays, maps, sets, several collections at once and the
document root, self-relations, and relations left unscoped because the target
lives in another system. Two real-world samples — a lending library catalogue
and an order book — put the whole set to work at once. All fourteen are
catalogued in the
[samples README](https://github.com/json-structure/primer-and-samples/blob/main/samples/relations/README.md).

The tooling stays here. Run
[`samples/validate-samples.ps1`](samples/validate-samples.ps1) to check the
meta-schema, every sample schema, every instance, and every relation; it expects
`json-structure/primer-and-samples` to be checked out beside this repository.

The relation check is the one a schema validator cannot make. A validator sees
one node at a time, so it can confirm that `cardinality` is one of two words and
that `targettype` resolves, but not that the target carries an identity, that a
scope holds the right type, or that an identity in an instance finds anything.
[`samples/check-relations.py`](samples/check-relations.py) makes those checks on
both the schema and the instance.

## Command Line Usage

Formatted text and HTML versions of the draft can be built using `make`.

```sh
$ make
```

Command line usage requires that you have the necessary software installed.  See
[the instructions](https://github.com/martinthomson/i-d-template/blob/main/doc/SETUP.md).

