# Variant Annotation Pipeline

A web-based application for genomic variant calling and annotation from FASTQ files.

## Overview

This pipeline automates the process of:
1. Aligning raw sequencing reads to a reference genome
2. Calling variants from the alignment
3. Annotating the variants with functional information
4. Generating an Excel report with filtered variant information

The system provides a simple web interface to upload FASTQ files and automatically processes them through the entire workflow.

## Features

- Web interface for easy file upload
- Automated alignment using BWA
- Variant calling with FreeBayes
- Comprehensive annotation using Annovar
- Structured Excel output with multiple sheets:
  - All variants
  - Exonic variants only
  - Rare variants (population frequency < 1%)
  - Summary statistics

## Prerequisites

- Docker
- Annovar (requires registration)
- Reference genome files (hg38)
- Sufficient disk space for genomic data processing

## Installation

1. Clone this repository
```bash
git clone https://github.com/yourusername/variant-annotation-pipeline.git
cd variant-annotation-pipeline
```

2. Download Annovar and place it in the project directory
   - Register at: https://www.openbioinformatics.org/annovar/annovar_download_form.php
   - Download and extract Annovar to a directory named `annovar`

3. Download required Annovar databases
```bash
cd annovar
perl annotate_variation.pl -buildver hg38 -downdb -webfrom annovar refGene humandb/
perl annotate_variation.pl -buildver hg38 -downdb -webfrom annovar exac03 humandb/
perl annotate_variation.pl -buildver hg38 -downdb -webfrom annovar avsnp147 humandb/
perl annotate_variation.pl -buildver hg38 -downdb -webfrom annovar dbnsfp30a humandb/
cd ..
```

4. Download the reference genome (hg38)
```bash
mkdir -p reference
cd reference
wget https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz
gunzip hg38.fa.gz
cd ..
```

5. Build the Docker container
```bash
docker build -t variant-pipeline .
```

## Usage

1. Start the server
```bash
docker run -p 5000:5000 -v /path/to/reference:/app/reference -v /path/to/annovar:/app/annovar variant-pipeline
```

2. Open a web browser and navigate to http://localhost:5000

3. Upload FASTQ files through the web interface

4. The pipeline will process the files and return an Excel spreadsheet with the annotated variants

## Troubleshooting

### Common Issues

1. **No space left on device**
   - Increase Docker disk space allocation
   - Mount external volumes with sufficient space
   - Clean up unused Docker volumes and images

2. **Missing tools or databases**
   - Verify all required tools are installed in the Docker image
   - Ensure Annovar databases are properly downloaded to the humandb directory
   - Check paths in the configuration match the Docker container structure

## File Structure

```
.
├── app.py                    # Flask application
├── Dockerfile                # Docker configuration
├── requirements.txt          # Python dependencies
├── templates/                # HTML templates for web interface
│   └── index.html
├── annovar/                  # Annovar installation directory
│   └── humandb/              # Annotation databases
└── reference/                # Reference genome files
```

## Technical Details

### Pipeline Steps

1. **Alignment**: BWA mem aligns FASTQ reads to the reference genome
2. **Sorting/Indexing**: Samtools sorts and indexes the resulting BAM file
3. **Variant Calling**: FreeBayes identifies variants from the alignment
4. **Normalization**: Bcftools normalizes variants for consistent representation
5. **Annotation**: Annovar adds functional information to variants
6. **Reporting**: Pandas creates a structured Excel file with filtered variants

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

* Uses Annovar for variant annotation
* Uses BWA, Samtools, FreeBayes, and other open-source bioinformatics tools
