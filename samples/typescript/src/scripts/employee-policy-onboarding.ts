#!/usr/bin/env node
/**
📝 EMPLOYEE POLICY ONBOARDING
==============================

This script exemplifies a typical HR onboarding workflow for new employees.
As an HR professional, it's necessary to ensure all new hires review and sign
required company policies before their start date. Manual distribution and
tracking of signatures is time-consuming and error-prone, especially when
onboarding multiple employees simultaneously.

This workflow automates policy distribution and signature collection. The script
processes each new employee individually - for every person in the CSV file, it
creates a signature envelope containing all company policy documents, sends it
via email with signature fields pre-configured, monitors the signing status, and
automatically downloads the signed documents once completed. Each employee's
signed policies are organized in their own folder, creating an audit-ready
archive of onboarding documentation.


NOTE: To run this script and see the complete workflow, you must provide a CSV file
with valid employee names and email addresses. The script will send actual signature
requests to these email addresses and wait for them to be signed.

EMPLOYEE CSV FORMAT:
  name,email
  John Doe,john.doe@company.com
  Jane Smith,jane.smith@company.com
  Bob Johnson,bob.johnson@company.com

USAGE:
  npm run employee-policy -- <policies_folder> <employees_csv>

  EXAMPLE:
    npm run employee-policy -- ./policies ./new_hires_jan2025.csv

  OUTPUT STRUCTURE:
    output/
     ├── john-doe/
     │   ├── signed-documents/
     │       ├── code-of-conduct-signed.pdf
     │       ├── confidentiality-agreement-signed.pdf
     │       └── audit-trail.pdf
     ├── jane-smith/
     │   ├── signed-documents/
 */

import { program } from 'commander';
import { stat, mkdir } from 'fs/promises';
import { join } from 'path';
import { SignAPIClient } from '../api/sign-api.js';
import {
  loadEmployeesFromCsv,
  loadPolicyDocumentsFromFolder,
  createEmployeeFolderName,
  createSignatureEnvelope,
  addSignatureFieldsToDocuments,
  sendAndMonitorEnvelope,
  downloadSignedDocument,
  logStep,
} from '../helpers/sign-helpers.js';

/**
 * Custom error for envelope not signed in time.
 */
class EnvelopeNotSignedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'EnvelopeNotSignedError';
  }
}

/**
 * Validate inputs and load data.
 * @param policiesFolder - Path to folder containing policy PDFs.
 * @param employeesCsv - Path to CSV file with employee data.
 * @returns Tuple of [outputFolder, employees, documents].
 */
async function validateAndSetupInputs(
  policiesFolder: string,
  employeesCsv: string
): Promise<[string, Array<{ name: string; email: string }>, Array<{ name: string; binary: Buffer; path: string }>]> {
  // Validate inputs
  try {
    const policiesStat = await stat(policiesFolder);
    if (!policiesStat.isDirectory()) {
      console.error(`❌ Policies folder not found: ${policiesFolder}`);
      process.exit(1);
    }
  } catch (error) {
    console.error(`❌ Policies folder not found: ${policiesFolder}`);
    process.exit(1);
  }

  try {
    await stat(employeesCsv);
  } catch (error) {
    console.error(`❌ Employees CSV not found: ${employeesCsv}`);
    process.exit(1);
  }

  // Display header
  const outputFolder = 'output';
  console.log('='.repeat(60));
  console.log('📝 SEND POLICIES TO EMPLOYEES');
  console.log('='.repeat(60));
  console.log(`Policies: ${policiesFolder}`);
  console.log(`Employees: ${employeesCsv}`);
  console.log(`Output: ${outputFolder}`);
  console.log('='.repeat(60));
  console.log();

  // Load employees and documents
  const employees = await loadEmployeesFromCsv(employeesCsv);
  console.log(`👥 Found ${employees.length} employee(s)\n`);

  const documents = await loadPolicyDocumentsFromFolder(policiesFolder);

  // Create output folder
  await mkdir(outputFolder, { recursive: true });

  return [outputFolder, employees, documents];
}

/**
 * Process onboarding workflow for a single employee.
 * @param signClient - Sign API client instance.
 * @param employee - Employee data object with 'name' and 'email'.
 * @param documents - Array of policy documents to send.
 * @param outputFolder - Base output folder for signed documents.
 * @param employeeNum - Current employee number (for display).
 * @param totalEmployees - Total number of employees (for display).
 */
async function processEmployeeOnboarding(
  signClient: SignAPIClient,
  employee: { name: string; email: string },
  documents: Array<{ name: string; binary: Buffer; path: string }>,
  outputFolder: string,
  employeeNum: number,
  totalEmployees: number
): Promise<void> {
  const { name, email } = employee;

  console.log(`\n[${employeeNum}/${totalEmployees}] ${name}`);

  // Create employee-specific output folder
  const employeeFolder = join(outputFolder, createEmployeeFolderName(name));
  await mkdir(employeeFolder, { recursive: true });

  // Create envelope and upload documents
  logStep('📝 Creating envelope...');
  const [envelopeId, documentIds] = await createSignatureEnvelope(
    signClient,
    documents,
    name,
    email
  );

  // Add participant (signer)
  logStep('👤 Adding signer...');
  const participantResponse = await signClient.createParticipant(envelopeId, {
    email,
    role: 'signer',
    name,
  });
  const participantId = participantResponse.ID;

  // Add signature fields to all documents
  logStep('✍️  Adding fields...');
  await addSignatureFieldsToDocuments(signClient, envelopeId, documentIds, participantId);

  // Send and monitor envelope
  logStep('📤 Sending...');
  const status = await sendAndMonitorEnvelope(signClient, envelopeId, email, 60);

  if (status !== 'sealed') {
    throw new EnvelopeNotSignedError(`Envelope not signed: ${status}`);
  }

  // Download signed documents
  logStep('📥 Downloading...');
  await downloadSignedDocument(signClient, envelopeId, employeeFolder, 'signed-policies.zip');

  console.log('  ✅ Completed\n');
}

program
  .name('employee-policy-onboarding')
  .description('Send company policy documents to employees for electronic signature via Sign API')
  .argument('<policies-folder>', 'Folder containing policy PDF documents')
  .argument('<employees-csv>', 'CSV file with employee data (name,email columns)')
  .action(async (policiesFolder: string, employeesCsv: string) => {
    try {
      // Validate inputs and load data
      const [outputFolder, employees, documents] = await validateAndSetupInputs(
        policiesFolder,
        employeesCsv
      );

      // Initialize Sign API client
      const signClient = new SignAPIClient();

      // Process each employee
      console.log('='.repeat(60));
      console.log(`📤 PROCESSING ${employees.length} EMPLOYEE(S)`);
      console.log('='.repeat(60));

      let successCount = 0;
      let failedCount = 0;

      for (let i = 0; i < employees.length; i++) {
        const employee = employees[i];

        try {
          await processEmployeeOnboarding(
            signClient,
            employee,
            documents,
            outputFolder,
            i + 1,
            employees.length
          );
          successCount++;
        } catch (error: any) {
          console.log(`  ❌ FAILED: ${error.message}\n`);
          failedCount++;
        }
      }

      // Display summary
      console.log('='.repeat(60));
      console.log(`✅ ${successCount} employee(s) completed`);
      if (failedCount > 0) {
        console.log(`❌ ${failedCount} failed`);
      }
      console.log(`📂 Output: ${outputFolder}`);
      console.log('='.repeat(60));
    } catch (error: any) {
      if (error.message === 'SIGINT') {
        console.log('\n\n⚠️  Interrupted by user');
        process.exit(1);
      }
      console.error(`\n❌ Error: ${error.message}`);
      process.exit(1);
    }
  });

// Handle SIGINT (Ctrl+C)
process.on('SIGINT', () => {
  console.log('\n\n⚠️  Interrupted by user');
  process.exit(1);
});

program.parse();
