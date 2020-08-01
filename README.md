# FLOnt: French Lexicon Ontology

This project aims at casting the French lexicon data from Wiktionary into an OWL ontology.

## Abstract

The [French Wiktionary](https://fr.wiktionary.org/wiki/Wiktionnaire:Page_d%E2%80%99accueil) is an immense source of lexical knowledge about the French language. Its community model allowed it to reach a broad coverage of the language, making it one of the best sources available online. Moreover, it's open-sourced. Yet, its content is hardly machine readable, preventing its usage in general application. We tackle this by parsing the Wiktionary data and populating an handcrafted ontology.

## Built With

- Input data: [Wiktionary](https://www.wiktionary.org/)
- Python OWL interface: [Owlready](https://pythonhosted.org/Owlready/)
- Ontology crafting: [Protégé](https://protege.stanford.edu/)
- Web application framework: [Django](https://www.djangoproject.com/)

## References

- [Hirst, G. (2009). *Ontology and the lexicon.* In Handbook on ontologies (pp. 269-292). Springer, Berlin, Heidelberg.](https://link.springer.com/chapter/10.1007/978-3-540-92673-3_12)
- [Cimiano, P., Buitelaar, P., McCrae, J., & Sintek, M. (2011). *LexInfo: A declarative model for the lexicon-ontology interface.* Journal of Web Semantics, 9(1), 29-51.](https://www.sciencedirect.com/science/article/pii/S1570826810000892)
