/**
 * Sign API client for Nitro Sign integrations (eSignature operations).
 */

import { readFile } from 'fs/promises';
import FormData from 'form-data';
import { BaseOAuthClient } from './base-client.js';

/**
 * Synchronous client for Nitro Sign API operations (eSignature/envelopes).
 */
export class SignAPIClient extends BaseOAuthClient {
  /**
   * Make authenticated API request returning JSON.
   * @param method - HTTP method.
   * @param endpoint - API endpoint path.
   * @param jsonData - Optional JSON payload.
   * @param params - Optional query parameters.
   * @returns Response data.
   */
  private async request(
    method: string,
    endpoint: string,
    jsonData?: Record<string, any>,
    params?: Record<string, any>
  ): Promise<any> {
    const token = await this.getToken();

    try {
      const response = await this.client.request({
        method,
        url: `${this.settings.platformBaseUrl}${endpoint}`,
        headers: {
          Authorization: `Bearer ${token}`,
        },
        data: jsonData,
        params,
      });

      return response.data;
    } catch (error: any) {
      // Try to get error details from response
      if (error.response?.data) {
        console.error(`   ❌ API Error Response:`, error.response.data);
      } else if (error.response?.text) {
        console.error(`   ❌ API Error (no JSON):`, error.response.text);
      }
      throw error;
    }
  }

  /**
   * Make authenticated API request returning binary data.
   * @param method - HTTP method.
   * @param endpoint - API endpoint path.
   * @param params - Optional query parameters.
   * @returns Binary response data as Buffer.
   */
  private async requestBytes(
    method: string,
    endpoint: string,
    params?: Record<string, any>
  ): Promise<Buffer> {
    const token = await this.getToken();

    const response = await this.client.request({
      method,
      url: `${this.settings.platformBaseUrl}${endpoint}`,
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params,
      responseType: 'arraybuffer',
    });

    return Buffer.from(response.data);
  }

  // ========== Envelope Management ==========

  /**
   * List all envelopes with cursor-based pagination.
   * @param pageAfter - Cursor token to get items after the last item from previous response.
   * @param pageBefore - Cursor token to get items before the last item from previous response.
   * @returns Object with 'items' (list of envelopes) and optional 'nextPage' (cursor token).
   */
  async listEnvelopes(pageAfter?: string, pageBefore?: string): Promise<any> {
    const params: Record<string, string> = {};
    if (pageAfter) {
      params.pageAfter = pageAfter;
    } else if (pageBefore) {
      params.pageBefore = pageBefore;
    }

    return this.request('GET', '/sign/envelopes', undefined, params);
  }

  /**
   * Create a new envelope.
   * @param envelopeData - Envelope configuration including name, documents, participants, fields.
   * @returns Created envelope with ID and status.
   */
  async createEnvelope(envelopeData: Record<string, any>): Promise<any> {
    return this.request('POST', '/sign/envelopes', envelopeData);
  }

  /**
   * Get envelope details by ID.
   * @param envelopeId - UUID of the envelope.
   * @returns Envelope details including status, participants, documents.
   */
  async getEnvelope(envelopeId: string): Promise<any> {
    return this.request('GET', `/sign/envelopes/${envelopeId}`);
  }

  /**
   * Update an envelope.
   * @param envelopeId - UUID of the envelope.
   * @param updates - Fields to update (name, participants, etc.).
   * @returns Updated envelope data.
   */
  async updateEnvelope(envelopeId: string, updates: Record<string, any>): Promise<any> {
    return this.request('PATCH', `/sign/envelopes/${envelopeId}`, updates);
  }

  /**
   * Delete an envelope by ID.
   * @param envelopeId - UUID of the envelope.
   */
  async deleteEnvelope(envelopeId: string): Promise<void> {
    const token = await this.getToken();

    await this.client.delete(`${this.settings.platformBaseUrl}/sign/envelopes/${envelopeId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  // ========== Document Management ==========

  /**
   * Upload a document to an envelope using form-data.
   * @param envelopeId - ID of the envelope.
   * @param filePath - Path to the PDF file to upload.
   * @param documentName - Optional custom name for the document.
   * @returns Created document with ID.
   */
  async createDocument(
    envelopeId: string,
    filePath: string,
    documentName?: string
  ): Promise<any> {
    const token = await this.getToken();

    if (!documentName) {
      documentName = filePath.split('/').pop() || 'document.pdf';
    }

    // Read the binary content of the PDF file
    const pdfBinary = await readFile(filePath);

    // Prepare metadata as JSON string
    const metadata = JSON.stringify({ name: documentName });

    // Prepare form-data with binary content
    const form = new FormData();
    form.append('metadata', metadata, {
      filename: 'metadata',
      contentType: 'application/json',
    });
    form.append('payload', pdfBinary, {
      filename: filePath.split('/').pop() || 'document.pdf',
      contentType: 'application/pdf',
    });

    const response = await this.client.post(
      `${this.settings.platformBaseUrl}/sign/envelopes/${envelopeId}/documents`,
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

  // ========== Participant Management ==========

  /**
   * Add a participant to an envelope.
   * @param envelopeId - ID of the envelope.
   * @param participantData - Participant configuration with role, email, name.
   * @returns Created participant with ID.
   */
  async createParticipant(
    envelopeId: string,
    participantData: Record<string, any>
  ): Promise<any> {
    return this.request(
      'POST',
      `/sign/envelopes/${envelopeId}/participants`,
      participantData
    );
  }

  // ========== Field Management ==========

  /**
   * Add a signature field to a document in an envelope.
   * @param envelopeId - ID of the envelope.
   * @param documentId - ID of the document.
   * @param fieldData - Field configuration with boundingBox, participantID, type, page.
   * @returns Created field with ID.
   */
  async createField(
    envelopeId: string,
    documentId: string,
    fieldData: Record<string, any>
  ): Promise<any> {
    return this.request(
      'POST',
      `/sign/envelopes/${envelopeId}/documents/${documentId}/fields`,
      fieldData
    );
  }

  // ========== Envelope Actions ==========

  /**
   * Send envelope to participants for signing.
   * This transitions the envelope from 'drafted' to 'sent' status.
   * @param envelopeId - UUID of the envelope.
   * @returns Updated envelope with 'sent' status.
   */
  async sendForSigning(envelopeId: string): Promise<any> {
    return this.request('POST', `/sign/envelopes/${envelopeId}:send-for-signing`);
  }

  /**
   * Cancel an envelope that was sent for signing.
   * @param envelopeId - UUID of the envelope.
   * @returns Envelope with 'cancelled' status.
   */
  async cancelEnvelope(envelopeId: string): Promise<any> {
    return this.request('PUT', `/sign/envelopes/${envelopeId}/cancel`);
  }

  /**
   * Send reminder notifications to pending signers.
   * @param envelopeId - UUID of the envelope.
   * @returns Confirmation of reminder sent.
   */
  async sendReminders(envelopeId: string): Promise<any> {
    return this.request('POST', `/sign/envelopes/${envelopeId}/reminders`);
  }

  // ========== Document Downloads ==========

  /**
   * Download the sealed (signed and completed) envelope.
   * @param envelopeId - UUID of the envelope.
   * @returns PDF bytes of the sealed document.
   */
  async downloadSealedEnvelope(envelopeId: string): Promise<Buffer> {
    return this.requestBytes('GET', `/sign/envelopes/${envelopeId}:download-sealed`);
  }

  /**
   * Download the original (unsigned) envelope documents.
   * @param envelopeId - UUID of the envelope.
   * @returns Original document bytes.
   */
  async downloadOriginalEnvelope(envelopeId: string): Promise<Buffer> {
    return this.requestBytes('GET', `/sign/envelopes/${envelopeId}:download-original`);
  }
}
