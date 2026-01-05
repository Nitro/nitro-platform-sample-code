#!/usr/bin/env node
/**
 * 🔐 BULK PASSWORD PROTECTION
 * ============================
 *
 * The script exemplifies a typical workflow for securing confidential documents.
 * As a security professional, it's essential to protect sensitive documents with
 * passwords before distributing them to authorized personnel, storing them in shared
 * drives, or archiving them for compliance purposes. Manually setting passwords on
 * individual files is tedious and inconsistent, leading to weak passwords or missed
 * files that remain unprotected.
 *
 * This workflow automates secure document protection. The script processes each PDF
 * file individually - for every document in the input folder, it applies robust
 * password encryption using a consistent password across all files. Each protected
 * file is saved to the output folder with the same filename, ensuring that the entire
 * batch of documents maintains uniform security standards. The result is a complete
 * set of password-protected PDFs ready for secure distribution or storage.
 *
 * DOCUMENT SECURITY STANDARDS:
 *   ✓ Password encryption (AES-256)
 *   ✓ Batch processing (entire folders)
 *   ✓ Consistent security (uniform password policy)
 *
 * USAGE:
 *   npm run bulk-password -- <input_folder> <output_folder> <password>
 *   # or with tsx:
 *   tsx src/scripts/bulk-password-protect.ts <input_folder> <output_folder> <password>
 *
 * EXAMPLE:
 *   npm run bulk-password -- ../../test_files/test-pdfs ./output MySecureP@ss123
 */

import { program } from 'commander';
import { writeFile } from 'fs/promises';
import { join } from 'path';
import { PlatformAPIClient } from '../api/platform-api.js';
import { validateAndSetup } from '../helpers/document-helpers.js';

program
  .name('bulk-password-protect')
  .description('Apply password protection to all PDF files in a directory')
  .argument('<input-folder>', 'Input folder containing PDF documents')
  .argument('<output-folder>', 'Output folder for protected PDFs')
  .argument('<password>', 'Password for protection (min 6 characters)')
  .action(async (inputFolder: string, outputFolder: string, password: string) => {
    try {
      // Validate password strength
      if (password.length < 6) {
        console.error('❌ Error: Password must be at least 6 characters long');
        process.exit(1);
      }

      // Validate and setup (only process PDF files)
      const files = await validateAndSetup(inputFolder, outputFolder, ['*.pdf']);
      console.log(`📋 Found ${files.length} PDF document(s) to protect\n`);

      // Initialize API client (loads credentials from .env)
      const client = new PlatformAPIClient();

      // Process each document
      let successCount = 0;
      let failedCount = 0;

      for (let i = 0; i < files.length; i++) {
        const pdfFile = files[i];
        const fileName = pdfFile.split('/').pop() || pdfFile;

        console.log(`[${i + 1}/${files.length}] Processing: ${fileName}`);

        try {
          // Apply password protection
          console.log('  🔐 Applying password protection...');
          const protectedPdf = await client.passwordProtect(pdfFile, password);

          // Save protected PDF
          const outputFile = join(outputFolder, fileName);
          await writeFile(outputFile, protectedPdf);

          console.log(`  ✅ Protected: ${fileName}\n`);
          successCount++;
        } catch (error: any) {
          console.log(`  ❌ FAILED: ${error.message}\n`);
          failedCount++;
        }
      }

      // Display summary
      console.log('='.repeat(60));
      console.log(`✅ ${successCount} document(s) password protected`);
      if (failedCount > 0) {
        console.log(`⚠️  ${failedCount} document(s) FAILED - remain unprotected!`);
      }
      console.log(`📂 Output: ${outputFolder}`);
      console.log(`🔑 Password: ${'*'.repeat(password.length)} (${password.length} characters)`);
      console.log('='.repeat(60));
    } catch (error: any) {
      console.error(`❌ Bulk password protection FAILED: ${error.message}`);
      process.exit(1);
    }
  });

program.parse();
