/**
 * Base client for API authentication with OAuth2.
 */

import axios, { AxiosInstance } from 'axios';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

/**
 * Token expiry buffer in seconds to account for clock skew and network latency.
 */
const TOKEN_EXPIRY_BUFFER_SECONDS = 60;

/**
 * OAuth2 token response model.
 */
interface TokenResponse {
  accessToken: string;
  expiresIn: number;
}

/**
 * Application settings for API authentication.
 */
interface Settings {
  platformClientId: string;
  platformClientSecret: string;
  platformBaseUrl: string;
}

/**
 * Base class for API clients with OAuth2 authentication.
 */
export class BaseOAuthClient {
  protected settings: Settings;
  private token: string | null = null;
  private tokenExpiry: number = 0;
  protected client: AxiosInstance;

  /**
   * Creates a new BaseOAuthClient instance.
   * @param settings - Optional settings override. If not provided, loads from environment variables.
   */
  constructor(settings?: Settings) {
    this.settings = settings || this.loadSettingsFromEnv();
    
    // Create axios instance with connection pooling
    this.client = axios.create({
      timeout: 30000,
      maxRedirects: 5,
    });
  }

  /**
   * Load settings from environment variables.
   * @returns Settings object populated from environment.
   * @throws Error if required environment variables are missing.
   */
  private loadSettingsFromEnv(): Settings {
    const clientId = process.env.PLATFORM_CLIENT_ID;
    const clientSecret = process.env.PLATFORM_CLIENT_SECRET;
    const baseUrl = process.env.PLATFORM_BASE_URL || 'https://api.gonitro.dev';

    if (!clientId || !clientSecret) {
      throw new Error(
        'Missing required environment variables: PLATFORM_CLIENT_ID and PLATFORM_CLIENT_SECRET must be set'
      );
    }

    return {
      platformClientId: clientId,
      platformClientSecret: clientSecret,
      platformBaseUrl: baseUrl,
    };
  }

  /**
   * Get or refresh OAuth2 access token.
   * @returns OAuth2 access token for API authentication.
   */
  protected async getToken(): Promise<string> {
    // Return cached token if still valid
    if (this.token && Date.now() / 1000 < this.tokenExpiry) {
      return this.token;
    }

    // Request new token
    const response = await this.client.post<TokenResponse>(
      `${this.settings.platformBaseUrl}/oauth/token`,
      {
        clientID: this.settings.platformClientId,
        clientSecret: this.settings.platformClientSecret,
      }
    );

    const tokenData = response.data;
    this.token = tokenData.accessToken;
    this.tokenExpiry = Date.now() / 1000 + tokenData.expiresIn - TOKEN_EXPIRY_BUFFER_SECONDS;

    return tokenData.accessToken;
  }
}
