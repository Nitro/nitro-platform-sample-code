#!/usr/bin/env node
/**
 * 🔄 SINGLE DOCUMENT CONVERSION
 * ==============================
 *
 * The script exemplifies a typical workflow for quick document format conversion.
 * As a business professional, you often need to convert individual
 * documents between formats for sharing, presentations, or compatibility requirements.
 * Whether converting a Word document to PDF for distribution, an Excel spreadsheet to
 * CSV for data processing, or a presentation to images for web display, manual
 * conversion through multiple applications is inefficient.
 *
 * This workflow provides instant document conversion. The script takes a single input
 * file and converts it to the specified output format using professional-grade
 * conversion algorithms. The result is a high-quality converted file that preserves
 * formatting, structure, and content fidelity, ready for immediate use.
 *
 * CONVERSION FEATURES:
 *   ✓ Multiple format support (PDF, DOCX, XLSX, PNG, etc.)
 *   ✓ High-fidelity conversion (preserves formatting)
 *
 * USAGE:
 *   npm run convert -- <input_file> <output_file> <format>
 *   # or with tsx:
 *   tsx src/scripts/convert-cli.ts <input_file> <output_file> <format>
 *
 * EXAMPLES:
 *   npm run convert -- document.docx document.pdf pdf
 *   npm run convert -- presentation.pptx slide.pdf pdf
 *   npm run convert -- spreadsheet.xlsx data.pdf pdf
 */

import { program } from 'commander';
import { stat, mkdir, writeFile } from 'fs/promises';
import { dirname } from 'path';
import { PlatformAPIClient, OutputFormat } from '../api/platform-api.js';

program
  .name('convert-cli')
  .description('Convert a document from one format to another using the Platform API')
  .argument('<input-file>', 'Input file to convert')
  .argument('<output-file>', 'Output file path')
  .argument('<format>', 'Target format for conversion (pdf, docx, xlsx, pptx, png)')
  .action(async (inputFile: string, outputFile: string, format: string) => {
    try {
      // Validate format
      const validFormats = Object.values(OutputFormat);
      if (!validFormats.includes(format.toLowerCase() as OutputFormat)) {
        console.error(`❌ Error: Invalid format '${format}'. Valid formats: ${validFormats.join(', ')}`);
        process.exit(1);
      }

      const toFormat = format.toLowerCase() as OutputFormat;

      // Validate input file exists
      try {
        await stat(inputFile);
      } catch (error) {
        console.error(`❌ Error: Input file not found: ${inputFile}`);
        process.exit(1);
      }

      // Create output directory if needed
      await mkdir(dirname(outputFile), { recursive: true });

      // Initialize API client (loads credentials from .env)
      const client = new PlatformAPIClient();

      // Get input file size
      const inputStat = await stat(inputFile);
      const inputFileName = inputFile.split('/').pop() || inputFile;

      // Convert document
      console.log(`🔄 Converting ${inputFileName} to ${toFormat.toUpperCase()}...`);
      const converted = await client.convert(inputFile, toFormat);

      // Save converted file
      await writeFile(outputFile, converted);

      // Display success message
      console.log('✅ Conversion successful!');
      console.log(`📄 Input:  ${inputFileName} (${inputStat.size.toLocaleString()} bytes)`);
      console.log(`📄 Output: ${outputFile.split('/').pop()} (${converted.length.toLocaleString()} bytes)`);
      console.log(`📂 Saved to: ${outputFile}`);
    } catch (error: any) {
      console.error(`❌ Conversion FAILED: ${error.message}`);
      process.exit(1);
    }
  });

program.parse();
