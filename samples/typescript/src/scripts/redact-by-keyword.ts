#!/usr/bin/env node
/**
 * 🔍 KEYWORD-BASED REDACTION
 * ===========================
 *
 * The script exemplifies a typical workflow for targeted content redaction.
 * As a compliance officer, you need to redact specific sensitive terms from documents
 * before external sharing or public disclosure. Whether removing client names, project
 * codenames, financial figures, or proprietary terminology, manually searching through
 * pages and applying redactions is tedious and risks missing instances, potentially
 * exposing confidential information.
 *
 * This workflow automates keyword-based redaction. The script searches the entire
 * PDF document for all specified keywords and phrases, identifies their exact
 * locations across all pages, then automatically applies permanent redactions to
 * remove them. Multiple keywords can be processed in a single pass, ensuring
 * comprehensive coverage. The result is a thoroughly redacted document ready for
 * safe distribution.
 *
 * KEYWORD REDACTION FEATURES:
 *   ✓ Multi-keyword search (process multiple terms)
 *   ✓ Whole document scanning (all pages)
 *   ✓ Exact location detection
 *   ✓ Permanent redaction (unrecoverable)
 *   ⏳ Case-insensitive matching (feature in development)
 *   ⏳ Regex pattern support (feature in development)
 *
 * USAGE:
 *   npm run redact-keyword -- <input_pdf> <output_pdf> <keyword1> [keyword2 ...]
 *   # or with tsx:
 *   tsx src/scripts/redact-by-keyword.ts <input_pdf> <output_pdf> <keyword1> [keyword2 ...]
 *
 * EXAMPLES:
 *   npm run redact-keyword -- contract.pdf redacted.pdf "confidential" "proprietary"
 *   npm run redact-keyword -- report.pdf clean.pdf "Project Zeus" "Client ABC"
 */

import { program } from 'commander';
import { stat, mkdir, writeFile, copyFile } from 'fs/promises';
import { dirname } from 'path';
import { PlatformAPIClient } from '../api/platform-api.js';

program
  .name('redact-by-keyword')
  .description('Redact specific keywords from PDF documents using text search')
  .argument('<input-pdf>', 'Input PDF file to redact')
  .argument('<output-pdf>', 'Output PDF file with redactions')
  .argument('<keywords...>', 'Keywords to search for and redact')
  .action(async (inputPdf: string, outputPdf: string, keywords: string[]) => {
    try {
      // Validate input file exists
      try {
        await stat(inputPdf);
      } catch (error) {
        console.error(`❌ Error: Input file not found: ${inputPdf}`);
        process.exit(1);
      }

      // Validate input is a PDF
      if (!inputPdf.toLowerCase().endsWith('.pdf')) {
        console.error('❌ Error: Input must be a PDF file');
        process.exit(1);
      }

      // Create output directory if needed
      await mkdir(dirname(outputPdf), { recursive: true });

      // Initialize API client (loads credentials from .env)
      const client = new PlatformAPIClient();

      // Step 1: Search for keywords in document
      console.log(`🔍 Searching for ${keywords.length} keyword(s) in ${inputPdf.split('/').pop()}...`);
      console.log(`   Keywords: ${keywords.map(k => `"${k}"`).join(', ')}`);

      const bboxData = await client.findTextBoxes(inputPdf, keywords);

      // Extract text box locations from response
      const textBoxes = bboxData.result?.textBoxes || [];

      if (textBoxes.length === 0) {
        console.log('ℹ️  No keyword matches found - copying original file');
        // Copy original file to output if no keywords found
        await copyFile(inputPdf, outputPdf);
        console.log(`✅ Saved: ${outputPdf.split('/').pop()}`);
        console.log(`📂 Output: ${outputPdf}`);
        return;
      }

      console.log(`🎯 Found ${textBoxes.length} keyword instance(s) to redact`);

      // Step 2: Prepare redaction coordinates
      console.log('🔒 Applying redactions...');
      const redactions = textBoxes.map((box: any) => ({
        pageIndex: box.pageIndex,
        boundingBox: box.boundingBox,
      }));

      // Step 3: Apply redactions to document
      const redactedPdf = await client.redact(inputPdf, redactions);

      // Save redacted PDF
      await writeFile(outputPdf, redactedPdf);

      // Display success message
      console.log('✅ Redaction successful!');
      console.log(`🔒 Redacted: ${textBoxes.length} instance(s)`);
      console.log(`📄 Input:  ${inputPdf.split('/').pop()}`);
      console.log(`📄 Output: ${outputPdf.split('/').pop()}`);
      console.log(`📂 Saved to: ${outputPdf}`);
    } catch (error: any) {
      console.error(`❌ Redaction FAILED: ${error.message}`);
      process.exit(1);
    }
  });

program.parse();
