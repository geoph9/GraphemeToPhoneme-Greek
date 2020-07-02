# available_phonemes: [a0, a1, b, d, dh, e0, e1, f, g, gh, h, hs, i0, i1, j, k,
#                      kj, l, m, n, ng, o0, o1, p, r, s, t, th, ts, u0, u1, v, z]

vowel_phonemes = ["a0", "a1", "e0", "e1", "i0", "i1", "o0", "o1", "u0", "u1"]

character_rules = {
    "α": "a0",
    "ά": "a1",
    "β": "v",
    "γ": "gh",  # but also j
    "δ": "dh",
    "ε": "e0",
    "έ": "e1",
    "ζ": "z",
    "η": "i0",
    "ή": "i1",
    "θ": "th",
    "ι": "i0",
    "ϊ": "i0",
    "ί": "i1",
    "ΐ": "i1",
    "κ": "k",
    "λ": "l",
    "μ": "m",
    "ν": "n",
    "ξ": "k s",
    "ο": "o0",
    "ό": "o1",
    "π": "p",
    "ρ": "r",
    "σ": "s",
    "ς": "s",
    "τ": "t",
    "υ": "i0",
    "ϋ": "i0",
    "ύ": "i1",
    "ΰ": "i1",
    "φ": "f",
    "χ": "h",  # but also hs
    "ψ": "p s",
    "ω": "o0",
    "ώ": "o1"
}

diphthong_rules = {
    "ου": "u0",
    "ού": "u1",
    "οϋ": "o0 i0",
    "οΰ": "o0 i1",
    "αι": "e0",
    "αί": "e0",
    "αΐ": "a0 i1",
    "αϊ": "a0 i0",
    "ει": "i0",
    "εί": "i1",
    "εΐ": "e0 i1",
    "εϊ": "e0 i0",
    "οι": "i0",
    "οί": "i1",
    "οΐ": "o0 i1",
    "οϊ": "o0 i0",
    "τζ": "d z",
    "γγ": "ng g",
    "γκ": "ng g",
    "ντ": "d",
    "μπ": "b",
    "κι": "kj",
    "τσ": "ts",
    "ια": "j a0",
    "ιά": "j a1",
    "ιο": "i o0",
    "ιό": "i o1"
}

triphthong_rules = {
    "νγκ": "n g",
    "για": "j a0",
    "γιά": "j a1"
}

single_letter_pronounciations = {
    "α": "άλφα",
    "ά": "άλφα",
    "β": "βήτα",
    "γ": "γάμμα",
    "δ": "δέλτα",
    "ε": "έψιλον",
    "έ": "έψιλον",
    "ζ": "ζήτα",
    "η": "η",
    "ή": "ή",
    "θ": "θήτα",
    "ι": "γιότα",
    "ί": "γιότα",
    "ϊ": "γιότα",
    "ΐ": "γιότα",
    "κ": "κάπα",
    "λ": "λάμδα",
    "μ": "μι",
    "ν": "νι",
    "ξ": "ξι",
    "ο": "ο",
    "ό": "όμικρον",
    "π": "πι",
    "ρ": "ρο",
    "σ": "σίγμα",
    "τ": "τάφ",
    "υ": "ύψιλον",
    "ύ": "ύψιλον",
    "ϋ": "ύψιλον",
    "ΰ": "ύψιλον",
    "φ": "φι",
    "χ": "χι",
    "ψ": "ψι",
    "ω": "ωμέγα",
    "ώ": "ωμέγα"
}

single_letter_words = ["ο", "η", "ή"]