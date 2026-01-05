#!/usr/bin/env node
/**
 * 🔒 PREPARE PDF FOR DISTRIBUTION
 * ================================
 *
 * The script exemplifies a typical workflow of marketing brochure distribution.
 * As a marketing professional, it's necessary to share company brochures externally
 * while ensuring they comply with corporate distribution standards. Word document
 * properties can expose internal information such as author names, template paths,
 * revision history, and company file structures that should remain confidential.
 *
 * This workflow automates compliant document preparation. The script processes each
 * file individually - for every brochure in the input folder, it converts the Word
 * document into PDF format, then compresses the file to reduce size and optimize
 * transmission, and finally removes all metadata properties to ensure privacy and
 * confidentiality. Each processed file is saved to the output folder, resulting in
 * distribution-ready brochures.
 *
 * COMPANY DISTRIBUTION STANDARDS:
 *   ✓ PDF format (prevents editing)
 *   ✓ Compressed (optimized file size)
 *   ✓ Properties removed (no metadata exposure)
 *   ⏳ Annotations removed (feature in development)
 *   ⏳ Accessibility enabled (feature in development)
 *
 * USAGE:
 *   npm run prepare-pdf -- <input_folder> <output_folder>
 *   # or with tsx:
 *   tsx src/scripts/prepare-pdf-for-distribution.ts <input_folder> <output_folder>
 *
 * EXAMPLE:
 *   npm run prepare-pdf -- ../../test_files/test-batch ./output
 */

import { program } from 'commander';
import { writeFile, unlink } from 'fs/promises';
import { join, parse } from 'path';
import { PlatformAPIClient, OutputFormat } from '../api/platform-api.js';
import { validateAndSetup } from '../helpers/document-helpers.js';

// Configuration: Properties to remove from PDFs
const PROPERTIES_TO_REMOVE = ['title', 'author', 'subject', 'keywords', 'creator', 'producer'];

program
  .name('prepare-pdf-for-distribution')
  .description('Prepare documents for distribution by converting to PDF and removing metadata')
  .argument('<input-folder>', 'Input folder containing documents')
  .argument('<output-folder>', 'Output folder for prepared PDFs')
  .action(async (inputFolder: string, outputFolder: string) => {
    try {
      // Validate and setup
      const files = await validateAndSetup(inputFolder, outputFolder);
      console.log(`📋 Found ${files.length} document(s) to process\n`);

      // Initialize API client (loads credentials from .env)
      const client = new PlatformAPIClient();

      // Process each document
      let successCount = 0;
      let failedCount = 0;

      for (let i = 0; i < files.length; i++) {
        const doc = files[i];
        const docName = doc.split('/').pop() || doc;
        const docBaseName = parse(doc).name;

        console.log(`[${i + 1}/${files.length}] Processing: ${docName}`);

        let tempPdf: string | null = null;

        try {
          // Step 1: Convert to PDF
          console.log('  🔐 Converting to PDF...');
          const pdfBytes = await client.convert(doc, OutputFormat.PDF);

          tempPdf = join(outputFolder, `${docBaseName}_temp.pdf`);
          await writeFile(tempPdf, pdfBytes);

          // Step 2: Compress PDF
          console.log('  📦 Compressing...');
          const compressedPdf = await client.compress(tempPdf, 2);
          await writeFile(tempPdf, compressedPdf);

          // Step 3: Remove metadata properties
          console.log('  🔒 Removing metadata...');
          const propertiesToClear: Record<string, string> = {};
          for (const prop of PROPERTIES_TO_REMOVE) {
            propertiesToClear[prop] = '';
          }
          const cleanPdf = await client.setProperties(tempPdf, propertiesToClear);

          // Save final PDF
          const finalPdf = join(outputFolder, `${docBaseName}.pdf`);
          await writeFile(finalPdf, cleanPdf);
          await unlink(tempPdf);

          console.log(`  ✅ Secured: ${parse(finalPdf).base}\n`);
          successCount++;
        } catch (error: any) {
          console.log(`  ❌ FAILED: ${error.message}\n`);
          failedCount++;
          if (tempPdf) {
            try {
              await unlink(tempPdf);
            } catch (e) {
              // Ignore cleanup errors
            }
          }
        }
      }

      // Display summary
      console.log('='.repeat(60));
      console.log(`✅ ${successCount} document(s) secured`);
      if (failedCount > 0) {
        console.log(`⚠️  ${failedCount} document(s) FAILED - do NOT distribute!`);
      }
      console.log(`📂 Output: ${outputFolder}`);
      console.log('='.repeat(60));
    } catch (error: any) {
      console.error(`❌ PDF preparation FAILED: ${error.message}`);
      process.exit(1);
    }
  });

program.parse();
