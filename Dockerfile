# ----------------------------------------------------------------------
# Compiling documentation
# ----------------------------------------------------------------------
FROM mambaorg/micromamba AS builder

user root

# Set the GA_KEY environment variable
ARG GA_KEY
ENV GA_KEY=$GA_KEY

# Print out the value of GA_KEY
RUN echo "GA_KEY value is: $GA_KEY"

# install packages
WORKDIR /src
COPY requirements.txt .
ENV PATH "$MAMBA_ROOT_PREFIX/bin:$PATH"
RUN micromamba install -y -n base -c anaconda -c conda-forge -c in-core \
    beautifulsoup4 \
    sphinx sphinx_rtd_theme \
    pyincore \
    -f requirements.txt

# copy code and generate documentation
COPY . ./
RUN sphinx-build -v -b html docs/source docs/build

# Run the insert_ga_to_header.py script to insert Google Analytics code
RUN python /src/docs/source/insert_ga_to_header.py


# ----------------------------------------------------------------------
# Building actual container
# ----------------------------------------------------------------------
FROM nginx

COPY --from=builder /src/docs/build/ /usr/share/nginx/html/doc/pyincore_data/
