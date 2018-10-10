# mXS

In short, mXS is a French NER Tagger.

## Description

mXS is a tool that you'll be able to easily install and use for French NER (Named Entity Recognition), it requires
- [TreeTagger](http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger) with French parameter file
- [scikit-learn](http://scikit-learn.org/stable/)

I did also successfully test for English (near state of the art performances) and German (still some work needed). It can also be used for any annotation task, as long as you provide a training corpus in the required format. Please send an email if you wish support or intend to train for another language.

Models that are available are base on the [ETAPE](http://www.afcp-parole.org/etape/docs/lrec-etape-12.pdf) evaluation campaign, which annotation are based on [Quaero annotation scheme](http://www.quaero.org/media/files/bibliographie/quaero-guide-annotation-2011.pdf). The "lazy" version of mXS tags a very restricted dataset with only persons, locations, organizations and products.

## Tagging French entities (ETAPE model) for very lazy people

If you have docker installed, it is very easy to use 

```bash
echo "Un test avec François Hollande en visite à Toulouse." | docker run -i guillaumeleclerc/mxs
```

Or with a file

```bash
docker run -i guillaumeleclerc/mxs < text_file
```

## Tagging French entities (ETAPE model) for (somehow less) lazy people

Configure TreeTagger path for mXS: comment out and set the TREETAGGER_PATH variable in file
```bash
bin/conf_machineExample.sh
```
E.g.
```bash
TREETAGGER_PATH=/mypath/to/folderof/treetagger
```

You may check if TreeTagger does properly work, e.g. in French
```bash
source bin/conf_machineExample.sh
echo "Je vais à Paris aujourd'hui." | $TREETAGGER_PATH/cmd/tree-tagger-french
```

Using command line, go into mxs root directory, and try (you'll have to wait a minute for lexicons to be loaded)
```bash
echo "Le président Barack Obama a été à Dakar, au Sénégal, en juin 2013." | ./bin/tagEtapeModelPLOP.sh
```

This command should output the folllowing annotation

`
Le <func> président </func> <pers> Barack Obama </pers> a été à <loc> Dakar </loc> , au <loc> Sénégal </loc> , en juin 2013 .
`

This model only provides PERS, LOC, ORG, FUNC entities (see below for fine-grained annotation). See my paper below for more information about annotation process, resources used, evaluation of accuracy (which indeed varies much depending on the quality of provided data), etc.

## Executing mXS from any location

It is more convenient to be able to execute mXS from other locations than its own path. For that purpose, you just need to define MXS_PATH environment variable (e.g. in command line, in your script or in .bashrc file)

```bash
export MXS_PATH=/mypath/to/folderof/mxs
```

You can now execute mXS script from anywhere using this variable as a prefix

```bash
echo "Un test avec François Hollande en visite à Toulouse." | $MXS_PATH/bin/tagEtapeModelPLOP.sh
```

This command outputs

`
Un test avec <pers> François Hollande </pers> en visite à <loc> Toulouse </loc> .
`

It is indeed possible to use mXS on a stream (e.g. corpus file) by redirecting input / output, for example

```bash
cat corpus.txt | $MXS_PATH/bin/tagEtapeModelPLOP.sh > corpus-tagged.txt
```

## Linking named entities

We are heading to Named Entity linking, it is currently provided as a beta version functionnality. For the moment, two data sources are used

- a local file in `dicos/links.json`
- a online request to dbpedia using [Wikiapi](https://github.com/richardasaurus/wiki-api).

Please keep in mind that unfortunately, the online request is currently unsufficiently disambiguated and may return incorrect links.

The command

```
echo "En 1930, John von Neumann a rencontré Alan Turing à Londres." | ./bin/linkEtapeModel.sh
```

Should output entity linked both from wikipedia (von Neumann) and from json file (Alan Turing)

`
En 1930 , <pers link="https://fr.wikipedia.org/wiki/John_von_Neumann">John von Neumann</pers> a rencontré <pers link="https://fr.wikipedia.org/wiki/Alan_Turing">Alan Turing</pers> à <loc> Londres </loc> .
`

## Obtaining fine-grained annotation

The Etape project also provides fine-grained and structured annotation of named entities. You may also use this model, at the cost of a much solower annotation process.
```bash
echo "Le président Barack Obama a été à Dakar, au Sénégal, en juin 2013." | ./bin/tagEtapeModel.sh
```

This command should output the folllowing full annotation, with components

`
Le <func.ind> <kind> président </kind> </func.ind> <pers.ind> <name.first> Barack </name.first> <name.last> Obama </name.last> </pers.ind> a été à <loc.adm.town> <name> Dakar </name> </loc.adm.town> , au <loc.adm.nat> <name> Sénégal </name> </loc.adm.nat> , en juin 2013 .
`

## Short how-to

This is an alpha release and I advise to contact me for installation / configuration / usage. My current problems are the availability of corpora for French, and adaptations of preprocessings (TreeTagger) for English. Anyway, let's write a very quick start guide.

You may want to only tag texts. In that case, provide the correct path for TreeTagger in
```bash
bin/conf_machineExample.sh
```

Source this file and the the configuration for the NER model (learned for French over [Etape](http://www.afcp-parole.org/etape.html) corpus)
```bash
source ./bin/conf_machineExample.sh
source ./bin/conf_EtapeModel.sh
```

Try to tag a text (be patient, loading models may take a few minutes), e.g.
```bash
echo "Le président Barack Obama a été en Afrique du Sud le 30 juillet 2013." | ./bin/tagSciKit.sh
```

For learning models over a specific corpus (and testing it), you'll need more configuration... first, compile the pattern extractor
```bash
make clean
make
```

Adapt configuration directives in
```bash
bin/conf_DatasetExample.sh
```

As previously, source configuration files
```bash
source ./bin/conf_machineExample.sh
source ./bin/conf_DatasetExample.sh
```

Then try the whole process
```bash
./bin/testCorpus.sh
```

Hopefully, the script testCorpus.sh is human-readable. In a few words, it should
1. Pre-process corpora
2. Extract patterns from train corpus
3. Learn regression models using scikit-learn
4. Use models to tag test corpus

Ok. This is very minimal. More to come, sooner or later, dependending on requests, with an examplified dataset...

## Pattern extractor

sminer extracts all sequences having a frequency greater than or equal to a minimum threshhold. Target (objective) items may be searched according to a confidence threshold and outputed (as "annotation rules").

Items may be form a hierarchy (subs): then specialisation is indicated using "/" operator (e.g. A/B and A/C are two items in data, and both are subtypes of A). The hierarchy may be a forest. Take care not to mix targets and none targets within same tree.

Patterns of identical frequencies which are generalization one of each other are grouped together, and only maximal (or minimal) patterns are to be extracted.

## Providing text along with non-analyzable input

A common but under-handled problem in NLP is the possibility to melt text and other non-analyzable input. For instance, if you have HTML file, you want the software to analyze text without processing tags, which are not natural language. mXS does partially support this by avoiding to analyze anything that is between `<_n` and `n_>` (and output it as it is).

Other replacements are available
- `<_b` will be replaced by a new line (e.g. you can add `<_bn_>` to create a new line in output),
- `<_t` and `t_>` will ignore contained text and be replaced in output by `<` and `>`
- same thing for `<_c` and `c_>` ignoring contained text and replace it by `[` and `]`

## Reference

If you use this software, here is a reference

Pattern Mining for Named Entity Recognition. Damien Nouvel, Jean-Yves Antoine, Nathalie Friburger. LNCS/LNAI Series volume 8387i (post-proceedings LTC 2011), 2014.

`
@article{PatternMiningNER_NouvelAntoineFriburger,  
  author = {Damien Nouvel and Jean-Yves Antoine and Nathalie Friburger},  
  title = {Pattern Mining for Named Entity Recognition},  
  journal = {LNCS/LNAI Series},  
  year = {2014},  
  volume = {8387i (post-proceedings LTC 2011)}  
}
`

## Debugging mXS

In case something goes wrong, you'll probably want to locate the problem. Here are some instruction that may help.
Indeed, check your numpy, scipy, scikit installations (try an import at Python CLI).

Export mXS path if not already done
```bash
export MXS_PATH=$(pwd)
```

Then source configuration files
```bash
source ./bin/conf_machineExample.sh
source ./bin/conf_EtapeModel.sh
```

Execute those commands to see at what stage you have a problem (be patient, $SEQUENCE_SCRIPT may load many lexicon)
```bash
sentence="Le président François Hollande a vu Barack Obama"
echo $sentence | $DATA_CORPUS_SCRIPT
echo $sentence | $DATA_CORPUS_SCRIPT | $PREPROCESS_SCRIPT
echo $sentence | $DATA_CORPUS_SCRIPT | $PREPROCESS_SCRIPT | $SEQUENCE_SCRIPT
echo $sentence | $DATA_CORPUS_SCRIPT | $PREPROCESS_SCRIPT | $SEQUENCE_SCRIPT | $MXS_BIN/applyRules.py -slb $CORPUS_MODEL/patterns.txt
echo $sentence | $DATA_CORPUS_SCRIPT | $PREPROCESS_SCRIPT | $SEQUENCE_SCRIPT | $MXS_BIN/applyRules.py -slb $CORPUS_MODEL/patterns.txt | $CORPUS_MERGE_SCRIPT
echo $sentence | $DATA_CORPUS_SCRIPT | $PREPROCESS_SCRIPT | $SEQUENCE_SCRIPT | $MXS_BIN/applyRules.py -slb $CORPUS_MODEL/patterns.txt | $CORPUS_MERGE_SCRIPT | $CORPUS_OUTPUT_SCRIPT
echo $sentence | $DATA_CORPUS_SCRIPT | $PREPROCESS_SCRIPT | $SEQUENCE_SCRIPT | $MXS_BIN/applyRules.py -slb $CORPUS_MODEL/patterns.txt | $CORPUS_MERGE_SCRIPT | $CORPUS_OUTPUT_SCRIPT | $CORPUS_DATA_SCRIPT
```
