/**
 * Sign API helper utilities for envelope operations.
 */

import { readFile, readdir, mkdir, writeFile } from 'fs/promises';
import { join } from 'path';
import { parse } from 'csv-parse/sync';
import AdmZip from 'adm-zip';
import { SignAPIClient } from '../api/sign-api.js';

/**
 * Convert employee name to folder-safe name.
 * @param employeeName - Full name like "John Doe".
 * @returns Folder-safe name like "john-doe".
 */
export function createEmployeeFolderName(employeeName: string): string {
  return employeeName.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '');
}

/**
 * Load employee list from CSV file.
 * @param csvPath - Path to CSV file with columns: name, email.
 * @returns Array of employee objects with 'name' and 'email'.
 * @throws Error if CSV format is invalid.
 */
export async function loadEmployeesFromCsv(csvPath: string): Promise<Array<{ name: string; email: string }>> {
  try {
    const content = await readFile(csvPath, 'utf-8');
    const records = parse(content, {
      columns: true,
      skip_empty_lines: true,
      trim: true,
    });

    const employees: Array<{ name: string; email: string }> = [];

    for (const row of records) {
      const name = row.name?.trim();
      const email = row.email?.trim();

      if (name && email && email.includes('@')) {
        employees.push({ name, email });
      }
    }

    if (employees.length === 0) {
      throw new Error('No valid employees found in CSV');
    }

    return employees;
  } catch (error: any) {
    throw new Error(`Failed to load employees from CSV: ${error.message}`);
  }
}

/**
 * Load all PDF files from the policies folder.
 * @param policiesFolder - Path to folder containing policy PDFs.
 * @returns Array of document objects with 'name', 'binary', and 'path'.
 */
export async function loadPolicyDocumentsFromFolder(policiesFolder: string): Promise<Array<{ name: string; binary: Buffer; path: string }>> {
  const files = await readdir(policiesFolder);
  const pdfFiles = files.filter(f => f.toLowerCase().endsWith('.pdf'));

  if (pdfFiles.length === 0) {
    throw new Error(`No PDF files found in ${policiesFolder}`);
  }

  console.log(`📂 Found ${pdfFiles.length} policy document(s)\n`);

  const documents: Array<{ name: string; binary: Buffer; path: string }> = [];

  for (const filename of pdfFiles) {
    const filePath = join(policiesFolder, filename);
    const binary = await readFile(filePath);

    documents.push({
      name: filename,
      binary,
      path: filePath,
    });
  }

  return documents;
}

/**
 * Upload documents to an existing envelope.
 * @param signClient - Sign API client instance.
 * @param envelopeId - ID of the envelope to upload to.
 * @param documents - Array of document objects with 'name', 'binary', 'path'.
 * @returns Array of document IDs.
 */
async function uploadDocumentsToEnvelope(
  signClient: SignAPIClient,
  envelopeId: string,
  documents: Array<{ name: string; binary: Buffer; path: string }>
): Promise<string[]> {
  const documentIds: string[] = [];

  for (const doc of documents) {
    // Use the createDocument method from SignAPIClient
    // We need to save to a temp file since createDocument expects a file path
    // For simplicity, we'll use the existing path
    const document = await signClient.createDocument(envelopeId, doc.path, doc.name);
    documentIds.push(document.ID);
  }

  return documentIds;
}

/**
 * Create envelope and upload documents.
 * @param signClient - Sign API client instance.
 * @param documents - Array of document objects.
 * @param employeeName - Full name of employee.
 * @param employeeEmail - Email address of employee.
 * @returns Tuple of [envelopeId, documentIds].
 */
export async function createSignatureEnvelope(
  signClient: SignAPIClient,
  documents: Array<{ name: string; binary: Buffer; path: string }>,
  employeeName: string,
  employeeEmail: string
): Promise<[string, string[]]> {
  // Create empty envelope
  const envelopeData = {
    name: `Company Policies - ${employeeName}`,
    mode: 'parallel',
    notification: {
      subject: 'Please sign: Company Policies',
      body: `Hello ${employeeName}, please review and sign the attached company policy documents.`,
    },
  };

  const envelope = await signClient.createEnvelope(envelopeData);
  const envelopeId = envelope.ID;

  // Upload documents to envelope
  const documentIds = await uploadDocumentsToEnvelope(signClient, envelopeId, documents);

  return [envelopeId, documentIds];
}

/**
 * Add signature and date fields to all documents in envelope.
 * @param signClient - Sign API client instance.
 * @param envelopeId - ID of the envelope.
 * @param documentIds - Array of document IDs to add fields to.
 * @param participantId - ID of the participant who will sign.
 */
export async function addSignatureFieldsToDocuments(
  signClient: SignAPIClient,
  envelopeId: string,
  documentIds: string[],
  participantId: string
): Promise<void> {
  for (const docId of documentIds) {
    // Add signature field (positioned bottom-left of page)
    // Coordinates: [x, y, width, height] in points (72 points = 1 inch)
    // Standard letter page: 612 x 792 points
    const signatureFieldData = {
      participantID: participantId,
      type: 'signature',
      label: 'Your Signature',
      page: 1,
      boundingBox: [50, 100, 200, 50], // Bottom area, safe coordinates
      required: true,
    };
    await signClient.createField(envelopeId, docId, signatureFieldData);

    // Add date field (positioned to the right of signature)
    const dateFieldData = {
      participantID: participantId,
      type: 'date',
      label: 'Date Signed',
      page: 1,
      boundingBox: [270, 100, 150, 50], // Next to signature, safe coordinates
      required: true,
      format: 'MM/DD/YYYY',
    };
    await signClient.createField(envelopeId, docId, dateFieldData);
  }
}

/**
 * Send envelope and monitor until signed or timeout.
 * @param signClient - Sign API client instance.
 * @param envelopeId - ID of envelope to send.
 * @param email - Email address of recipient.
 * @param timeoutMinutes - Maximum time to wait (default: 60).
 * @returns Final status: 'sealed', 'cancelled', 'timeout', or 'error'.
 */
export async function sendAndMonitorEnvelope(
  signClient: SignAPIClient,
  envelopeId: string,
  email: string,
  timeoutMinutes: number = 60
): Promise<string> {
  // Send envelope
  await signClient.sendForSigning(envelopeId);

  // Log send time and status
  const sendTime = new Date().toISOString().replace('T', ' ').substring(0, 19);
  console.log(`     ✅ Sent at: ${sendTime}`);
  console.log(`     📧 Email sent to: ${email}`);
  console.log(`     🔗 Envelope ID: ${envelopeId}`);

  // Check initial status
  const envelope = await signClient.getEnvelope(envelopeId);
  console.log(`     📊 Status: ${envelope.status}`);

  // Monitor for completion
  console.log('  ⏳ Waiting for signature...');
  console.log(`     ⏱️  Checking every 30 seconds (timeout: ${timeoutMinutes} minutes)`);

  const status = await monitorEnvelope(signClient, envelopeId, timeoutMinutes);

  // Log final status
  const completionTime = new Date().toISOString().replace('T', ' ').substring(0, 19);
  console.log(`     📊 Final status: ${status}`);
  console.log(`     🕐 Completed at: ${completionTime}`);

  return status;
}

/**
 * Monitor envelope until signed, cancelled, or timeout.
 * @param signClient - Sign API client instance.
 * @param envelopeId - ID of envelope to monitor.
 * @param timeoutMinutes - Maximum time to wait (default: 60).
 * @returns Final status: 'sealed', 'cancelled', 'timeout', or 'error'.
 */
export async function monitorEnvelope(
  signClient: SignAPIClient,
  envelopeId: string,
  timeoutMinutes: number = 60
): Promise<string> {
  const checkInterval = 30; // seconds
  const maxChecks = Math.floor((timeoutMinutes * 60) / checkInterval);

  for (let i = 0; i < maxChecks; i++) {
    try {
      const envelope = await signClient.getEnvelope(envelopeId);
      const status = envelope.status;

      if (status === 'sealed') {
        return 'sealed';
      }
      if (['cancelled', 'rejected', 'deleted'].includes(status)) {
        return 'cancelled';
      }

      if (i < maxChecks - 1) {
        await new Promise(resolve => setTimeout(resolve, checkInterval * 1000));
      }
    } catch (error: any) {
      console.error(`      ⚠️  Error checking status: ${error.message}`);
      return 'error';
    }
  }

  return 'timeout';
}

/**
 * Download sealed envelope and extract signed documents.
 * @param signClient - Sign API client instance.
 * @param envelopeId - ID of sealed envelope.
 * @param outputFolder - Employee-specific output folder.
 * @param documentName - Name for the saved file (should end with .zip).
 * @returns Path to extracted documents folder.
 */
export async function downloadSignedDocument(
  signClient: SignAPIClient,
  envelopeId: string,
  outputFolder: string,
  documentName: string
): Promise<string> {
  // Download sealed envelope (returns ZIP file)
  const zipBytes = await signClient.downloadSealedEnvelope(envelopeId);

  // Save as temporary ZIP file
  if (!documentName.endsWith('.zip')) {
    documentName = documentName.replace('.pdf', '.zip');
  }

  const tempZipPath = join(outputFolder, documentName);
  await writeFile(tempZipPath, zipBytes);

  // Extract the ZIP contents
  const extractFolder = join(outputFolder, 'signed-documents');
  await mkdir(extractFolder, { recursive: true });

  const zip = new AdmZip(tempZipPath);
  zip.extractAllTo(extractFolder, true);

  // Delete the ZIP file after extraction
  const fs = await import('fs/promises');
  await fs.unlink(tempZipPath);

  // Save envelope metadata
  const envelope = await signClient.getEnvelope(envelopeId);
  const jsonPath = join(outputFolder, 'envelope-info.json');
  await writeFile(jsonPath, JSON.stringify(envelope, null, 2));

  console.log(`     💾 Extracted to: ${extractFolder}`);

  return extractFolder;
}

/**
 * Log a processing step with consistent formatting.
 * @param message - The message to log.
 * @param emoji - Optional emoji to prepend (default: none).
 */
export function logStep(message: string, emoji?: string): void {
  const prefix = emoji ? `${emoji} ` : '  ';
  console.log(`${prefix}${message}`);
}
