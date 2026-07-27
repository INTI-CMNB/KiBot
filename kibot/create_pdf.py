# -*- coding: utf-8 -*-
# Copyright (c) 2022-2026 Salvador E. Tropea
# Copyright (c) 2022-2026 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2022 Albin Dennevi (create_pdf_from_pages)
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Base idea for create_pdf_from_pages: https://gitlab.com/dennevi/Board2Pdf/ (Released as Public Domain)
# Base idea for split_pdf: Gemini 3.1 Pro
import os
from . import PyPDF2
from . import log

logger = log.get_logger()


def create_pdf_from_pages(input_files, output_fn, forced_width=None):
    output = PyPDF2.PdfFileWriter()
    # Collect all pages
    open_files = []
    for filename in input_files:
        file = open(filename, 'rb')
        open_files.append(file)
        pdf_reader = PyPDF2.PdfFileReader(file)
        num_pages = len(pdf_reader.pages)
        for page in range(num_pages):
            page_obj = pdf_reader.getPage(page)
            if forced_width is not None:
                width = float(page_obj.mediaBox.getWidth())*25.4/72
                scale = round(forced_width/width, 4)
                logger.debugl(1, 'PDF scale {} ({} -> {})'.format(scale, width, forced_width))
                if abs(1.0-scale) > 0.0001:
                    page_obj.scaleBy(scale)
            page_obj.compressContentStreams()
            output.addPage(page_obj)
    # Write all pages to a file
    with open(output_fn, 'wb') as pdf_output:
        output.write(pdf_output)
    # Close the files
    for f in open_files:
        f.close()


def split_pdf(input_pdf):
    with open(input_pdf, "rb") as infile:
        reader = PyPDF2.PdfFileReader(infile)
        num_pages = len(reader.pages)

        if num_pages == 1:
            return [input_pdf]

        base_name = os.path.splitext(input_pdf)[0]
        created = []
        for i in range(num_pages):
            writer = PyPDF2.PdfFileWriter()
            writer.addPage(reader.pages[i])

            output_filepath = f"{base_name}-{i+1}.pdf"

            created.append(output_filepath)
            with open(output_filepath, "wb") as outfile:
                writer.write(outfile)
    return created
