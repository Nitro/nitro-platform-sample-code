#!/usr/bin/env node
/**
 📁 BATCH DOCUMENT CONVERSION
=============================

The script exemplifies a typical workflow for document format standardization.
As a IT administrator, it's essential to convert
large collections of documents into standardized formats for archival, compliance,
or system integration purposes. Manually converting individual files through desktop
applications is time-consuming and impractical for large document sets, often leading
to inconsistent results and wasted effort.

This workflow automates bulk document conversion. The script processes files
individually - for every document matching the specified pattern in the input folder,
it converts the file to the target format (PDF, DOCX, XLSX, PNG, JPG, etc.) using
high-fidelity conversion algorithms. Each converted file is saved to the output
folder with the same base name but the new format extension, resulting in a
complete batch of standardized documents.

BATCH CONVERSION FEATURES:
  ✓ Multiple format support (PDF, DOCX, XLSX, PNG, JPG, etc.)
  ✓ Flexible file pattern matching (*.docx, *.xlsx, *.pptx, *.pdf.)

USAGE:
   npm run batch -- <input_folder> <output_folder> <format> [pattern]
  
EXAMPLES:
   npm run batch -- ../../test_files/test-batch ./output pdf "*.docx"
   npm run batch -- ./documents ./converted png "*"
 */

import { program } from 'commander';
import { writeFile } from 'fs/promises';
import { join, parse } from 'path';
import { PlatformAPIClient, OutputFormat } from '../api/platform-api.js';
import { validateAndSetup } from '../helpers/document-helpers.js';

program
  .name('batch-process')
  .description('Process multiple documents in batch, converting them to a specified format')
  .argument('<input-folder>', 'Input folder containing documents to convert')
  .argument('<output-folder>', 'Output folder for converted documents')
  .argument('<format>', 'Target format for conversion (pdf, docx, xlsx, pptx)')
  .argument('[pattern]', 'File pattern to match (e.g., "*.docx", "*.pdf", "*")', '*')
  .action(async (inputFolder: string, outputFolder: string, format: string, pattern: string) => {
    try {
      // Validate format
      const validFormats = Object.values(OutputFormat);
      if (!validFormats.includes(format.toLowerCase() as OutputFormat)) {
        console.error(`❌ Error: Invalid format '${format}'. Valid formats: ${validFormats.join(', ')}`);
        process.exit(1);
      }

      const toFormat = format.toLowerCase() as OutputFormat;

      // Validate and setup with custom pattern
      const files = await validateAndSetup(inputFolder, outputFolder, [pattern]);
      console.log(`📋 Found ${files.length} file(s) matching '${pattern}'\n`);

      // Initialize API client (loads credentials from .env)
      const client = new PlatformAPIClient();

      // Process each document
      let successCount = 0;
      let failedCount = 0;

      for (let i = 0; i < files.length; i++) {
        const filePath = files[i];
        const fileName = filePath.split('/').pop() || filePath;
        const fileBaseName = parse(filePath).name;

        console.log(`[${i + 1}/${files.length}] Processing: ${fileName}`);

        try {
          // Convert to target format
          console.log(`  🔄 Converting to ${toFormat.toUpperCase()}...`);
          const converted = await client.convert(filePath, toFormat);

          // Save converted file
          const outputFile = join(outputFolder, `${fileBaseName}.${toFormat}`);
          await writeFile(outputFile, converted);

          console.log(`  ✅ Converted: ${parse(outputFile).base}\n`);
          successCount++;
        } catch (error: any) {
          console.log(`  ❌ FAILED: ${error.message}\n`);
          failedCount++;
        }
      }

      // Display summary
      console.log('='.repeat(60));
      console.log(`✅ ${successCount} file(s) converted to ${toFormat.toUpperCase()}`);
      if (failedCount > 0) {
        console.log(`⚠️  ${failedCount} file(s) FAILED to convert!`);
      }
      console.log(`📂 Output: ${outputFolder}`);
      console.log('='.repeat(60));
    } catch (error: any) {
      console.error(`❌ Batch processing FAILED: ${error.message}`);
      process.exit(1);
    }
  });

program.parse();
