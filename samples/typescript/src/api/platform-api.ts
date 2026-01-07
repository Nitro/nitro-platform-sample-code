/**
 * Platform API client for Nitro Platform integrations.
 */

import { readFile } from 'fs/promises';
import FormData from 'form-data';
import axios from 'axios';
import { BaseOAuthClient } from './base-client.js';
import { lookup } from 'mime-types';

/**
 * Supported output formats for document conversion.
 */
export enum OutputFormat {
  PDF = 'pdf',
  DOCX = 'docx',
  XLSX = 'xlsx',
  PPTX = 'pptx',
  PNG = 'png',
}

/**
 * Type for API endpoints.
 */
type Endpoint = 'conversions' | 'extractions' | 'transformations';

/**
 * Synchronous client for Nitro Platform API operations.
 */
export class PlatformAPIClient extends BaseOAuthClient {
  /**
   * Make API request with file upload.
   * @param endpoint - API endpoint (conversions, extractions, transformations).
   * @param method - API method to call.
   * @param filePath - Path to file to upload.
   * @param params - Optional parameters for the method.
   * @returns Parsed JSON response.
   */
  private async request(
    endpoint: Endpoint,
    method: string,
    filePath: string,
    params?: Record<string, any>
  ): Promise<any> {
    const token = await this.getToken();
    
    // Read file and detect MIME type
    const fileBuffer = await readFile(filePath);
    const fileName = filePath.split('/').pop() || 'file';
    const mimeType = lookup(filePath) || 'application/octet-stream';

    // Create form data
    const form = new FormData();
    form.append('file', fileBuffer, {
      filename: fileName,
      contentType: mimeType,
    });
    form.append('method', method);
    form.append('params', JSON.stringify(params || {}));

    const response = await this.client.post(
      `${this.settings.platformBaseUrl}/${endpoint}`,
      form,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          ...form.getHeaders(),
        },
      }
    );

    return response.data;
  }

  /**
   * Make API request and return raw bytes from result file URL.
   * @param endpoint - API endpoint.
   * @param method - API method to call.
   * @param filePath - Path to file to upload.
   * @param params - Optional parameters for the method.
   * @returns File content as Buffer.
   */
  private async requestBytes(
    endpoint: Endpoint,
    method: string,
    filePath: string,
    params?: Record<string, any>
  ): Promise<Buffer> {
    const result = await this.request(endpoint, method, filePath, params);

    // Download from S3 URL
    const downloadUrl = result.result.file.URL;
    const downloadResponse = await axios.get(downloadUrl, {
      responseType: 'arraybuffer',
    });

    return Buffer.from(downloadResponse.data);
  }

  /**
   * Convert document to specified format.
   * @param filePath - Path to input file.
   * @param toFormat - Target format (pdf, docx, xlsx, pptx, png).
   * @returns Converted file as Buffer.
   */
  async convert(filePath: string, toFormat: OutputFormat): Promise<Buffer> {
    return this.requestBytes('conversions', 'convert', filePath, { to: toFormat });
  }

  /**
   * Extract text from document.
   * @param filePath - Path to input file.
   * @returns Extracted text data.
   */
  async extractText(filePath: string): Promise<any> {
    return this.request('extractions', 'extract-text', filePath);
  }

  /**
   * Extract form data from PDF.
   * @param filePath - Path to PDF file.
   * @returns Extracted form data.
   */
  async extractForms(filePath: string): Promise<any> {
    return this.request('extractions', 'extract-forms', filePath);
  }

  /**
   * Extract table data from PDF.
   * @param filePath - Path to PDF file.
   * @returns Extracted table data.
   */
  async extractTables(filePath: string): Promise<any> {
    return this.request('extractions', 'extract-tables', filePath);
  }

  /**
   * Detect PII and return bounding boxes.
   * @param filePath - Path to input file.
   * @param language - Language code (default: 'en').
   * @returns PII detection results with bounding boxes.
   */
  async detectPii(filePath: string, language: string = 'en'): Promise<any> {
    return this.request('extractions', 'extract-pii-bounding-boxes', filePath, { language });
  }

  /**
   * Find bounding boxes for specified text strings.
   * @param filePath - Path to input file.
   * @param texts - Array of text strings to search for.
   * @returns Bounding boxes for found text.
   */
  async findTextBoxes(filePath: string, texts: string[]): Promise<any> {
    return this.request('extractions', 'extract-text-bounding-boxes', filePath, { texts });
  }

  /**
   * Redact specified bounding boxes.
   * @param filePath - Path to input file.
   * @param redactions - Array of redaction specifications.
   * @returns Redacted file as Buffer.
   */
  async redact(filePath: string, redactions: any[]): Promise<Buffer> {
    return this.requestBytes('transformations', 'redact', filePath, { redactions });
  }

  /**
   * Add password protection to PDF.
   * @param filePath - Path to PDF file.
   * @param password - Password to set.
   * @returns Protected PDF as Buffer.
   */
  async passwordProtect(filePath: string, password: string): Promise<Buffer> {
    return this.requestBytes('transformations', 'protect', filePath, {
      ownerPassword: password,
      userPassword: password,
    });
  }

  /**
   * Compress PDF.
   * @param filePath - Path to PDF file.
   * @param level - Compression level (1-3, default: 2).
   * @returns Compressed PDF as Buffer.
   */
  async compress(filePath: string, level: number = 2): Promise<Buffer> {
    return this.requestBytes('transformations', 'compress', filePath, { level });
  }

  /**
   * Set or clear PDF metadata properties.
   * @param filePath - Path to PDF file.
   * @param properties - Object with property names and values.
   * @returns Modified PDF as Buffer.
   */
  async setProperties(filePath: string, properties: Record<string, string>): Promise<Buffer> {
    return this.requestBytes('transformations', 'set-properties', filePath, properties);
  }

  /**
   * Merge multiple PDFs.
   * @param filePaths - Array of paths to PDF files to merge.
   * @returns Merged PDF as Buffer.
   */
  async merge(filePaths: string[]): Promise<Buffer> {
    const token = await this.getToken();
    
    // Create form data with multiple files
    const form = new FormData();
    
    for (const filePath of filePaths) {
      const fileBuffer = await readFile(filePath);
      const fileName = filePath.split('/').pop() || 'file';
      form.append('file', fileBuffer, { filename: fileName });
    }
    
    form.append('method', 'merge');
    form.append('params', '{}');

    const response = await this.client.post(
      `${this.settings.platformBaseUrl}/transformations`,
      form,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          ...form.getHeaders(),
        },
        responseType: 'arraybuffer',
      }
    );

    return Buffer.from(response.data);
  }
}
