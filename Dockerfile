# ----------------------------------------------------------------------
# Compiling documentation
# ----------------------------------------------------------------------
FROM mambaorg/micromamba AS builder

user root

# install packages
WORKDIR /src
COPY requirements.txt .
ENV PATH "$MAMBA_ROOT_PREFIX/bin:$PATH"
RUN micromamba install -y -n base -c anaconda -c conda-forge -c in-core \
    sphinx sphinx_rtd_theme \
    pyincore \
    -f requirements.txt

# copy code and generate documentation
COPY . ./
RUN sphinx-build -v -b html docs/source docs/build

# ----------------------------------------------------------------------
# Building actual container
# ----------------------------------------------------------------------
FROM nginx

COPY --from=builder /src/docs/build/ /usr/share/nginx/html/doc/pyincore_data/
