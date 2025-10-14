/**
 * Environment configuration
 * Validates and exports environment variables with proper types
 */

interface EnvConfig {
  // API Configuration
  apiBaseUrl: string;
  apiTimeout: number;

  // AWS Cognito Configuration
  cognito: {
    region: string;
    userPoolId: string;
    clientId: string;
  };

  // Application Settings
  appName: string;
  appVersion: string;
  environment: string;

  // CloudFront (optional)
  cloudFrontDomain?: string;
}

const getEnvVar = (key: string, required = true): string => {
  const value = import.meta.env[key];

  if (!value && required) {
    throw new Error(`Missing required environment variable: ${key}`);
  }

  return value || '';
};

export const env: EnvConfig = {
  apiBaseUrl: getEnvVar('VITE_API_BASE_URL'),
  apiTimeout: parseInt(getEnvVar('VITE_API_TIMEOUT', false) || '30000', 10),

  cognito: {
    region: getEnvVar('VITE_COGNITO_REGION'),
    userPoolId: getEnvVar('VITE_COGNITO_USER_POOL_ID'),
    clientId: getEnvVar('VITE_COGNITO_CLIENT_ID'),
  },

  appName: getEnvVar('VITE_APP_NAME'),
  appVersion: getEnvVar('VITE_APP_VERSION'),
  environment: getEnvVar('VITE_ENV'),

  cloudFrontDomain: getEnvVar('VITE_CLOUDFRONT_DOMAIN', false),
};

// Validate configuration on load
const validateConfig = () => {
  const errors: string[] = [];

  if (!env.apiBaseUrl.startsWith('https://')) {
    errors.push('API Base URL must use HTTPS');
  }

  if (env.apiTimeout < 1000 || env.apiTimeout > 60000) {
    errors.push('API timeout must be between 1000ms and 60000ms');
  }

  if (!env.cognito.userPoolId.match(/^[\w-]+_[\w]+$/)) {
    errors.push('Invalid Cognito User Pool ID format');
  }

  if (errors.length > 0) {
    console.error('Configuration validation errors:', errors);
    throw new Error(`Invalid configuration: ${errors.join(', ')}`);
  }
};

// Run validation
validateConfig();

export default env;
