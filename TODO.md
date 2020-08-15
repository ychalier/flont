# To-Do List

## Simple Additions

- [ ] **[ontology]** Parse definitions for verbal inflections, to make up for missing `{{fr-verbe-flexion}}` templates and incomplete conjugation tables.
- [ ] **[ontology]** Insert labels (relation names, POS names, etc.) as annotations within the ontology, through the `rdfs:label` property.
- [ ] **[ontology]** Clearly state the grammatical gender and number of adjectives, pronouns, etc., to allow for gender selection queries.
- [ ] **[ontology]** Express definition dependency (characterized by precisions of type `flont:RelationshipBetweenDefinition`) through a new relation between lexical senses.
- [x] **[ontology]** When a definition is parsed as an inflection description, do not output a lexical sense for it.
- [ ] **[ontology]** When a level 3 section contains pronunciation information, associate it to entries without pronunciation information instead of the literal (for consistency).
- [ ] **[webapp]** Support symmetric relationships (such as synonymy).
- [ ] **[webapp]** Template parsing for clean etymology display.
- [ ] **[webapp]** Link WordReference to translate French literals into English.

## Ideas

- [ ] **[webapp]** Serve portions of the data through a REST API.

## Polysemy Balancing

One literal may have several lexical entries. Most of the time, it has one per grammatical part-of-speech, but there can be more, if the senses are really different. Each lexical entry then has several lexical senses, one per actual sense of the word. The idea is to split very different senses as lexical entries and then slightly different senses as lexical senses. This is typically done in lexicons. But Wiktionary's articles do not all follow the same idea of polysemy, leading to inconsistent partitioning of the senses:

- the literal [accordeur](//chalier.fr/flont/graph/_accordeur) ('tuner') has two lexical entries, one for [the person tuning an instrument](//chalier.fr/flont/graph/_accordeur_nCom1) and one for [the device used for tuning instruments](//chalier.fr/flont/graph/_accordeur_nCom2) (I am not sure splitting the two is necessary),
- the entry [salade (i)](//chalier.fr/flont/graph/_salade_nCom1) ('lettuce' or 'nonsense') has a lexical sense for [the vegetable](//chalier.fr/flont/graph/_salade_nCom1.2) and another one for [the false speech](//chalier.fr/flont/graph/_salade_nCom1.5) (I would think those senses are different enough for splitting).

Such inconsistencies belittle the quality of the ontology. I am not sure what should be done about that. A simple fix would be grouping together all entries with the same POS, at the cost of semantic knowledge. Unsupervised partitioning seems like a hard task though. There could be literature about that.

## Re-targeting `flont:isLinkedTo` Properties

Those are the properties such as `flont:isSynonymOf`, `flont:hasHolonym`, etc. Currently, they are instantiated between lexical entries and literals. This is due to Wiktionary's article format. Roughly, each lexical entry is a section in the article (one article per literal); `flont:isLinkedTo` properties are extracted from hyperlinks (usually only stating the literal) within the subsections. Depending on what is done with polysemy balancing, it could be a nice improvement to change the domain/range of those properties so they can be more meaningful.
