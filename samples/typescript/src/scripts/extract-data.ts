#!/usr/bin/env node
/**
📊 DOCUMENT DATA EXTRACTION
============================

The script exemplifies a typical workflow for intelligent document data extraction.
As a data analyst, you need to extract structured
data from PDF documents - whether form fields from applications, surveys, and
questionnaires, or table data from reports, invoices, and financial statements.
Manual data entry is error-prone and time-consuming, especially when processing
hundreds of documents for analysis or database import.

This workflow automates data extraction using AI-powered document understanding.
The script analyzes PDF documents and intelligently identifies and extracts either
form fields (with field names and values) or table structures (with rows, columns,
and cell contents). The extracted data is saved as structured JSON, ready for
immediate integration with databases, spreadsheets, or analytics pipelines.

DATA EXTRACTION FEATURES:
  ✓ AI-powered form field extraction
  ✓ Intelligent table detection and extraction
  ✓ Structured JSON output format
  ✓ High accuracy recognition
  
  
USAGE:
   npm run extract -- <mode> <input_pdf> <output_json>
  
MODES:
   forms  - Extract form fields (name-value pairs)
   tables - Extract table data (rows and columns)
 
EXAMPLES:
   npm run extract -- forms application.pdf data.json
   npm run extract -- tables invoice.pdf tables.json
 */

import { program } from 'commander';
import { stat, mkdir, writeFile } from 'fs/promises';
import { dirname } from 'path';
import { PlatformAPIClient } from '../api/platform-api.js';

program
  .name('extract-data')
  .description('Extract structured data (forms or tables) from PDF documents')
  .argument('<mode>', "Extraction mode: 'forms' or 'tables'")
  .argument('<input-pdf>', 'Input PDF file')
  .argument('<output-json>', 'Output JSON file')
  .action(async (mode: string, inputPdf: string, outputJson: string) => {
    try {
      // Normalize mode to lowercase
      mode = mode.toLowerCase();

      // Validate mode
      if (!['forms', 'tables'].includes(mode)) {
        console.error("❌ Error: Mode must be 'forms' or 'tables'");
        process.exit(1);
      }

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
      await mkdir(dirname(outputJson), { recursive: true });

      // Initialize API client (loads credentials from .env)
      const client = new PlatformAPIClient();

      // Extract data based on mode
      let data: any;
      let dataType: string;

      if (mode === 'forms') {
        console.log(`📋 Extracting form fields from ${inputPdf.split('/').pop()}...`);
        data = await client.extractForms(inputPdf);
        dataType = 'form fields';
      } else {
        // mode === 'tables'
        console.log(`📊 Extracting table data from ${inputPdf.split('/').pop()}...`);
        data = await client.extractTables(inputPdf);
        dataType = 'tables';
      }

      // Count extracted items
      const result = data.result || {};
      const itemCount =
        mode === 'forms'
          ? (result.fields || []).length
          : (result.tables || []).length;

      // Save extracted data as JSON
      await writeFile(outputJson, JSON.stringify(data, null, 2), 'utf-8');

      // Display success message
      console.log('✅ Extraction successful!');
      console.log(`📊 Extracted: ${itemCount} ${dataType}`);
      console.log(`📄 Input:  ${inputPdf.split('/').pop()}`);
      console.log(`📄 Output: ${outputJson.split('/').pop()}`);
      console.log(`📂 Saved to: ${outputJson}`);
    } catch (error: any) {
      console.error(`❌ Extraction FAILED: ${error.message}`);
      process.exit(1);
    }
  });

program.parse();
