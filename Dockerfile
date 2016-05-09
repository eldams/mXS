FROM python:2
RUN pip install numpy scipy scikit-learn
RUN mkdir -p /root/mXS && mkdir -p /root/treetagger
WORKDIR /root/treetagger
ADD "http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.tar.gz" .
ADD "http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz" .
ADD "http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh" .
ADD "http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/french-par-linux-3.2-utf8.bin.gz" .
RUN bash install-tagger.sh
ENV TREETAGGER_PATH="/root/treetagger" \
    MXS_PATH="/root/mXS"
ENV PATH /root/mXS/bin:$PATH
WORKDIR /root/mXS
ADD . ./
ENTRYPOINT "tagEtapeModelPLOP.sh"
