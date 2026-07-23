import unittest

from calamus_citations import (
    CitationCluster,
    CitationItem,
    CitationLookup,
    citation_lookup_at,
    cited_keys,
    format_pandoc_citation,
    is_valid_citation_key,
    normalize_locator,
    parse_citation_clusters,
)


class CitationSyntaxTests(unittest.TestCase):
    def test_format_simple_and_locator_citations(self):
        self.assertEqual(format_pandoc_citation("ratzinger1968"), "[@ratzinger1968]")
        self.assertEqual(
            format_pandoc_citation("ratzinger1968", "  , p. 42  "),
            "[@ratzinger1968, p. 42]",
        )
        self.assertEqual(normalize_locator("chap. 2\n section 3"), "chap. 2 section 3")

    def test_format_rejects_invalid_or_terminal_punctuation_key(self):
        self.assertFalse(is_valid_citation_key("bad key"))
        self.assertFalse(is_valid_citation_key("bad-key."))
        with self.assertRaises(ValueError):
            format_pandoc_citation("bad key")
        with self.assertRaises(ValueError):
            format_pandoc_citation("bad-key.")
        with self.assertRaises(ValueError):
            format_pandoc_citation("alpha2020", "p. 42]")

    def test_parse_single_grouped_and_bare_citations(self):
        text = "One [@alpha2020, p. 2]; two [see @beta2021; @gamma2022, chap. 4]; bare @delta2023."
        clusters = parse_citation_clusters(text)
        self.assertEqual(tuple(cluster.keys for cluster in clusters), (
            ("alpha2020",),
            ("beta2021", "gamma2022"),
            ("delta2023",),
        ))
        self.assertTrue(clusters[0].bracketed)
        self.assertFalse(clusters[-1].bracketed)
        for cluster in clusters:
            self.assertEqual(text[cluster.start:cluster.end], cluster.raw)
            for item in cluster.items:
                self.assertEqual(text[item.start:item.end], item.key)

    def test_parser_ignores_fenced_and_inline_code(self):
        text = (
            "Visible [@alpha2020].\n"
            "`inline [@beta2021]`\n"
            "```markdown\n[@gamma2022]\n```\n"
            "Visible @delta2023.\n"
        )
        self.assertEqual(cited_keys(text), ("alpha2020", "delta2023"))

    def test_lookup_prefers_key_under_cursor_in_group(self):
        text = "Grouped [@alpha2020; @beta2021, p. 9]."
        alpha = citation_lookup_at(text, text.index("alpha") + 2)
        beta = citation_lookup_at(text, text.index("beta") + 2)
        between = citation_lookup_at(text, text.index(";"))
        self.assertEqual((alpha.status, alpha.key), ("unique", "alpha2020"))
        self.assertEqual((beta.status, beta.key), ("unique", "beta2021"))
        self.assertEqual(between.status, "ambiguous")
        self.assertEqual(between.keys, ("alpha2020", "beta2021"))

    def test_lookup_single_cluster_works_from_locator_and_bracket(self):
        text = "Read [@alpha2020, p. 42] now."
        for position in (text.index("["), text.index("p. 42") + 2):
            lookup = citation_lookup_at(text, position)
            self.assertEqual((lookup.status, lookup.key), ("unique", "alpha2020"))

    def test_lookup_none_for_code_or_plain_text(self):
        self.assertEqual(citation_lookup_at("plain text", 3).status, "none")
        coded = "`[@alpha2020]`"
        self.assertEqual(citation_lookup_at(coded, coded.index("alpha")).status, "none")

    def test_cited_keys_deduplicate_in_document_order(self):
        text = "[@beta2021] [@alpha2020; @beta2021] @gamma2022"
        self.assertEqual(cited_keys(text), ("beta2021", "alpha2020", "gamma2022"))

    def test_model_validation(self):
        item = CitationItem("alpha2020", 2, 11)
        cluster = CitationCluster(0, 12, (item,), "[@alpha2020]")
        self.assertEqual(cluster.keys, ("alpha2020",))
        self.assertEqual(CitationLookup("unique", "alpha2020", ("alpha2020",), cluster).key, "alpha2020")
        with self.assertRaises(ValueError):
            CitationItem("bad key", 0, 2)
        with self.assertRaises(ValueError):
            CitationCluster(0, 1, (), "")
        with self.assertRaises(ValueError):
            CitationLookup("invalid")

    def test_non_string_and_non_integer_inputs_fail_closed(self):
        with self.assertRaises(TypeError):
            parse_citation_clusters(None)
        with self.assertRaises(TypeError):
            citation_lookup_at("text", 1.5)
        with self.assertRaises(TypeError):
            cited_keys(None)


if __name__ == "__main__":
    unittest.main()
