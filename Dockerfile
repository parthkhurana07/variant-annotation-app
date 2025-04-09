FROM ubuntu:20.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    build-essential \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libbz2-dev \
    liblzma-dev \
    libssl-dev \
    python3 \
    python3-pip \
    python3-dev \
    bwa \
    samtools \
    git \
    perl \
    cmake \
    autoconf \
    pkg-config \
    bcftools \
    freebayes \
    libvcflib-tools libvcflib-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Python 3 as default
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install Python packages
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Create app directory
WORKDIR /app

# Install Annovar (Note: Annovar must be downloaded manually due to licensing)
RUN mkdir -p /app/annovar /app/annovar/humandb

# Create directories for reference data, uploads, and results
RUN mkdir -p /app/reference /app/uploads /app/results

# Copy the application code and templates
COPY app.py /app/
COPY templates /app/templates/

# Define entry point and expose port
CMD ["python3", "app.py"]
EXPOSE 5000
