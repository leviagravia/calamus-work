# Calamus Work Policy

Status: active

## 1. Project identity

The target project is Calamus.

This repository is not Centurio and is not a rename experiment.

## 2. Existing local directory

A local directory named `~/Projects/calamus` already exists.

Therefore this working area uses:

```text
~/Projects/calamus-work
```

## 3. Operating rule

Work must start from Calamus as Calamus.

Avoid:

- unnecessary renaming
- duplicate hardening without a new risk
- packaging-first workflows before functional value exists
- creating fork identity before proving actual improvement

Prefer:

- source audit
- small patches
- direct functional value
- tests that cover the changed behavior
- package work only when the source change justifies it

## 4. Installed package

Installed Calamus is treated as the user-facing baseline.

Development work must not silently break or replace installed Calamus.
