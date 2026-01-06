#!/usr/bin/env node
/** 
🔒 SMART PII REDACTION
======================
 
The script exemplifies a typical workflow for protecting sensitive customer information.
As a compliance officer, it's essential to review and redact
personally identifiable information (PII) from documents before sharing them with
third parties, storing them in public systems, or using them for analysis. Manual
redaction is time-consuming and error-prone, potentially missing sensitive data like
social security numbers, phone numbers, addresses, or email addresses.

This workflow automates compliant document redaction. The script processes each PDF
file individually - for every document in the input folder, it uses AI-powered PII
detection to identify all instances of sensitive information across all pages, then
automatically applies redactions to permanently remove this data. Each processed file
is saved to the output folder with all PII securely redacted, ready for safe sharing
or archival.

PRIVACY COMPLIANCE STANDARDS:
  ✓ AI-powered PII detection (SSN, phone, email, address)
  ✓ Automatic redaction (permanent removal)
  ✓ Batch processing (entire folders)
 
USAGE:
  npm run smart-redact -- <input_folder> <output_folder>
 
EXAMPLE:
  npm run smart-redact -- ../../test_files/test-pdfs ./output
 */

import { program } from 'commander';
import { writeFile, copyFile } from 'fs/promises';
import { join } from 'path';
import { PlatformAPIClient } from '../api/platform-api.js';
import { validateAndSetup } from '../helpers/document-helpers.js';

program
  .name('smart-redact-pii')
  .description('Automatically detect and redact PII (personally identifiable information) from PDFs')
  .argument('<input-folder>', 'Input folder containing PDF documents')
  .argument('<output-folder>', 'Output folder for redacted PDFs')
  .action(async (inputFolder: string, outputFolder: string) => {
    try {
      // Validate and setup (only process PDF files)
      const files = await validateAndSetup(inputFolder, outputFolder, ['*.pdf']);
      console.log(`📋 Found ${files.length} PDF document(s) to process`);

      // Initialize API client
      const client = new PlatformAPIClient();

      // Process each document
      let successCount = 0;
      let failedCount = 0;
      let totalPiiCount = 0;

      for (let i = 0; i < files.length; i++) {
        const pdfFile = files[i];
        const fileName = pdfFile.split('/').pop() || pdfFile;

        console.log(`[${i + 1}/${files.length}] Processing: ${fileName}`);

        try {
          // Step 1: Detect PII in the document
          console.log('  🔍 Detecting PII...');
          const piiData = await client.detectPii(pdfFile);

          // Extract PII bounding boxes from response
          const piiBoxes = piiData.result?.PIIBoxes || [];

          if (piiBoxes.length === 0) {
            console.log('  ℹ️  No PII detected - copying original file');

            // Copy original file to output if no PII found
            const outputFile = join(outputFolder, fileName);
            await copyFile(pdfFile, outputFile);

            console.log(`  ✅ Saved: ${fileName}`);
            successCount++;
            continue;
          }

          console.log(`  🎯 Found ${piiBoxes.length} PII instance(s)`);
          totalPiiCount += piiBoxes.length;

          // Step 2: Prepare redaction coordinates
          console.log('  🔒 Applying redactions...');
          const redactions = piiBoxes.map((box: any) => ({
            pageIndex: box.pageIndex,
            boundingBox: box.boundingBox,
          }));

          // Step 3: Apply redactions to document
          const redactedPdf = await client.redact(pdfFile, redactions);

          // Save redacted PDF
          const outputFile = join(outputFolder, fileName);
          await writeFile(outputFile, redactedPdf);

          console.log(`  ✅ Redacted: ${fileName}`);
          successCount++;
        } catch (error: any) {
          console.log(`  ❌ FAILED: ${error.message}`);
          failedCount++;
        }
      }

      // Display summary
      console.log('='.repeat(60));
      console.log(`✅ ${successCount} document(s) processed`);
      console.log(`🔒 ${totalPiiCount} total PII instance(s) redacted`);
      if (failedCount > 0) {
        console.log(`⚠️  ${failedCount} document(s) FAILED - review manually!`);
      }
      console.log(`📂 Output: ${outputFolder}`);
      console.log('='.repeat(60));
    } catch (error: any) {
      console.error(`❌ Smart redaction FAILED: ${error.message}`);
      process.exit(1);
    }
  });

program.parse();
