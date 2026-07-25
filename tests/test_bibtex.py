import unittest

from calamus_bibtex import (
    ACTION_IMPORT, ACTION_MERGE, ACTION_NEW_KEY, ACTION_REPLACE, ACTION_SKIP,
    BIBLATEX, BIBTEX, COLLISION_ALIAS, COLLISION_INPUT, COLLISION_KEY,
    BibImportDecision, apply_import_decisions, build_import_preview,
    decode_latex, export_references, map_bib_entry, parse_bibliography,
    parse_person_names,
)
from calamus_references import ReferenceRecord


class BibtexPureTests(unittest.TestCase):
    def test_parser_resolves_strings_and_reports_non_entry_blocks(self):
        text = r'''@string{cup = {Cambridge University Press}}
@comment{preserve as diagnostic evidence}
@preamble{"prefix" # cup}
@book{ratzinger1968,
  author = {Ratzinger, Joseph},
  title = {Introduction to {Christianity}},
  year = 1968,
  publisher = cup,
  keywords = {Faith; theology}
}
'''
        library = parse_bibliography(text, BIBTEX)
        self.assertEqual(len(library.entries), 1)
        self.assertEqual(dict(library.entries[0].fields)["publisher"], "Cambridge University Press")
        self.assertEqual(len(library.comments), 1)
        self.assertEqual(len(library.preambles), 1)
        mapped = map_bib_entry(library.entries[0], BIBTEX)
        self.assertTrue(mapped.importable)
        self.assertEqual(mapped.record.authors, ("Ratzinger, Joseph",))
        self.assertEqual(mapped.record.tags, ("Faith", "theology"))

    def test_duplicate_key_and_field_are_explicit_not_last_wins(self):
        text = '''@book{same, title={First}, title={Second}}
@article{same, title={Third}}
'''
        library = parse_bibliography(text, BIBTEX)
        codes = tuple(item.code for item in library.diagnostics)
        self.assertIn("duplicate-field", codes)
        self.assertIn("duplicate-key", codes)
        self.assertEqual(dict(library.entries[0].fields)["title"], "First")
        preview = build_import_preview(library, ())
        self.assertIsNone(preview.items[0].record)
        self.assertEqual(preview.items[0].default_action, ACTION_SKIP)

    def test_malformed_field_does_not_hide_following_valid_block(self):
        text = '''@book{bad, title {Missing equals}}
@book{good, title={Valid}}
'''
        library = parse_bibliography(text, BIBTEX)
        self.assertEqual(tuple(entry.key for entry in library.entries), ("bad", "good"))
        self.assertTrue(any(item.code == "invalid-field" for item in library.diagnostics))
        self.assertTrue(map_bib_entry(library.entries[1], BIBTEX).importable)

    def test_latex_and_names_are_conservative_and_unicode(self):
        decoded, warnings = decode_latex(r'Jos\'{e} and M\\uller and \\unknown{X}')
        self.assertIn("José", decoded)
        self.assertIn("unknown", decoded)
        self.assertTrue(warnings)
        names, _ = parse_person_names(r'{World Health Organization} and Ludwig van Beethoven and de la Cruz, Juan')
        self.assertEqual(names[0], "World Health Organization")
        self.assertEqual(names[1], "van Beethoven, Ludwig")
        self.assertEqual(names[2], "de la Cruz, Juan")

    def test_mapping_preserves_unknown_fields_and_original_lossy_type(self):
        library = parse_bibliography(
            '''@dataset{data2025, title={Corpus}, author={Doe, Jane}, custom={Value}, date={2025-07}}''',
            BIBLATEX,
        )
        mapped = map_bib_entry(library.entries[0], BIBLATEX)
        self.assertEqual(mapped.record.type, "other")
        self.assertEqual(mapped.record.year, "2025-07")
        self.assertIn(("bib-entry-type", "dataset"), mapped.record.extra_fields)
        self.assertIn(("custom", "Value"), mapped.record.extra_fields)

    def test_collision_preview_and_actions_are_explicit(self):
        existing = (
            ReferenceRecord(key="same", title="Old", aliases=("alias",), doi="10.1/x"),
            ReferenceRecord(key="probable", title="Duplicate", year="2020", authors=("Doe, Jane",)),
        )
        library = parse_bibliography('''
@book{same, title={New}, publisher={P}}
@book{alias, title={Alias collision}}
@book{other, title={Duplicate}, year={2020}, author={Doe, Jane}}
@book{dup, title={One}}
@book{dup, title={Two}}
@book{fresh, title={Fresh}}
''', BIBTEX)
        preview = build_import_preview(library, existing)
        by_key = {}
        for item in preview.items:
            by_key.setdefault(item.source_key, []).append(item)
        self.assertEqual(by_key["same"][0].collision, COLLISION_KEY)
        self.assertEqual(by_key["alias"][0].collision, COLLISION_ALIAS)
        self.assertTrue(all(item.collision == COLLISION_INPUT for item in by_key["dup"]))
        decisions = (
            BibImportDecision(by_key["same"][0].index, ACTION_MERGE),
            BibImportDecision(by_key["alias"][0].index, ACTION_NEW_KEY),
            BibImportDecision(by_key["other"][0].index, ACTION_SKIP),
            BibImportDecision(by_key["dup"][0].index, ACTION_NEW_KEY),
            BibImportDecision(by_key["dup"][1].index, ACTION_SKIP),
            BibImportDecision(by_key["fresh"][0].index, ACTION_IMPORT),
        )
        projection = apply_import_decisions(preview, existing, decisions)
        self.assertEqual(projection.merged, 1)
        self.assertEqual(projection.rekeyed, 2)
        self.assertEqual(projection.imported, 3)
        same = next(record for record in projection.records if record.key == "same")
        self.assertEqual(same.title, "Old")
        self.assertEqual(same.publisher, "P")
        self.assertIn("fresh", tuple(record.key for record in projection.records))

    def test_collision_defaults_are_non_destructive_and_merge_preserves_incoming_key_alias(self):
        existing = (ReferenceRecord(key="local", title="Same", year="2020", authors=("Doe, Jane",)),)
        library = parse_bibliography(
            '@book{incoming, title={Same}, year={2020}, author={Doe, Jane}, doi={10.1/x}}',
            BIBTEX,
        )
        preview = build_import_preview(library, existing)
        item = preview.items[0]
        self.assertEqual(item.default_action, ACTION_SKIP)
        projection = apply_import_decisions(
            preview,
            existing,
            (BibImportDecision(item.index, ACTION_MERGE),),
        )
        merged = projection.records[0]
        self.assertEqual(merged.key, "local")
        self.assertIn("incoming", merged.aliases)
        self.assertEqual(merged.doi, "10.1/x")

    def test_canonical_export_can_be_reimported_without_key_or_title_loss(self):
        original = ReferenceRecord(
            key="guardini1950", title="The End of the Modern World",
            type="book", authors=("Guardini, Romano",), year="1950",
            publisher="Publisher", tags=("modernity",), doi="10.1/test",
        )
        artifact = export_references((original,), BIBLATEX)
        library = parse_bibliography(artifact.text, BIBLATEX)
        mapped = map_bib_entry(library.entries[0], BIBLATEX).record
        self.assertEqual(mapped.key, original.key)
        self.assertEqual(mapped.title, original.title)
        self.assertEqual(mapped.authors, original.authors)
        self.assertEqual(mapped.year, original.year)
        self.assertEqual(mapped.tags, original.tags)
        self.assertEqual(mapped.doi, original.doi)

    def test_export_is_deterministic_and_explicit_by_mode(self):
        record = ReferenceRecord(
            key="r1", title="A & B", type="journal-article",
            authors=("Doe, Jane",), year="2025-07", container_title="Journal",
            tags=("faith", "history"), extra_fields=(("custom", "value"),),
        )
        biblatex = export_references((record,), BIBLATEX)
        bibtex = export_references((record,), BIBTEX)
        self.assertIn("@article{r1,", biblatex.text)
        self.assertIn("date = {2025-07}", biblatex.text)
        self.assertIn("journaltitle = {Journal}", biblatex.text)
        self.assertIn("journal = {Journal}", bibtex.text)
        self.assertIn("custom = {value}", biblatex.text)
        self.assertEqual(biblatex, export_references((record,), BIBLATEX))

    def test_parenthesis_entry_does_not_close_on_parenthesis_inside_braces(self):
        library = parse_bibliography(
            '@book(parenthesized, title={Faith) and Reason}, year=2025)\n'
            '@book{following, title={Following}}',
            BIBTEX,
        )
        self.assertEqual(tuple(entry.key for entry in library.entries), ("parenthesized", "following"))
        self.assertEqual(dict(library.entries[0].fields)["title"], "Faith) and Reason")

    def test_mode_specific_alternate_fields_are_preserved_and_reported(self):
        library = parse_bibliography(
            """@article{dual,
  title={Dual fields},
  date={2025-07},
  year={2024},
  journaltitle={Canonical Journal},
  journal={Legacy Journal},
  location={Rome},
  address={London},
  annotation={Primary annotation},
  note={Legacy note}
}""",
            BIBLATEX,
        )
        mapped = map_bib_entry(library.entries[0], BIBLATEX)
        self.assertEqual(mapped.record.year, "2025-07")
        self.assertEqual(mapped.record.container_title, "Canonical Journal")
        self.assertEqual(mapped.record.location, "Rome")
        self.assertEqual(mapped.record.annotation, "Primary annotation")
        extras = dict(mapped.record.extra_fields)
        self.assertEqual(extras["year"], "2024")
        self.assertEqual(extras["journal"], "Legacy Journal")
        self.assertEqual(extras["address"], "London")
        self.assertEqual(extras["note"], "Legacy note")
        self.assertTrue(any(item.code == "preserved-alternate-field" for item in mapped.diagnostics))

    def test_export_round_trip_preserves_corporate_author_and_backslash(self):
        original = ReferenceRecord(
            key="corp",
            title="Institutional work",
            authors=("World Health Organization",),
            file_path=r"C:\Research\source.pdf",
        )
        artifact = export_references((original,), BIBLATEX)
        self.assertIn("author = {{World Health Organization}}", artifact.text)
        self.assertIn(r"file = {C:\textbackslash{}Research\textbackslash{}source.pdf}", artifact.text)
        mapped = map_bib_entry(
            parse_bibliography(artifact.text, BIBLATEX).entries[0],
            BIBLATEX,
        ).record
        self.assertEqual(mapped.authors, original.authors)
        self.assertEqual(mapped.file_path, original.file_path)

    def test_extended_common_latex_accents_are_decoded(self):
        decoded, warnings = decode_latex(r"\v{S}imek, Erd\H{o}s, Dvo\v{r}\'{a}k")
        self.assertEqual(decoded, "Šimek, Erdős, Dvořák")
        self.assertEqual(warnings, ())

    def test_export_reports_lossy_type_date_and_extra_field_collision(self):
        record = ReferenceRecord(
            key="web",
            title="Online",
            type="website",
            year="2025-07",
            annotation="Native note",
            extra_fields=(("note", "Original note"),),
        )
        artifact = export_references((record,), BIBTEX)
        joined = "\n".join(artifact.warnings)
        self.assertIn("website is represented as misc", joined)
        self.assertIn("full date", joined)
        self.assertIn("extra field 'note' was omitted", joined)



if __name__ == "__main__":
    unittest.main()
