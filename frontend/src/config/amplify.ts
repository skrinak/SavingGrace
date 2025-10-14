/**
 * AWS Amplify Configuration
 * Sets up AWS Cognito for authentication
 */

import { Amplify } from 'aws-amplify';
import { env } from './env';

export const configureAmplify = () => {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: env.cognito.userPoolId,
        userPoolClientId: env.cognito.clientId,
        loginWith: {
          email: true,
        },
        signUpVerificationMethod: 'code',
        userAttributes: {
          email: {
            required: true,
          },
          given_name: {
            required: true,
          },
          family_name: {
            required: true,
          },
          phone_number: {
            required: false,
          },
        },
        mfa: {
          status: 'optional',
          totpEnabled: true,
          smsEnabled: false,
        },
        passwordFormat: {
          minLength: 8,
          requireLowercase: true,
          requireUppercase: true,
          requireNumbers: true,
          requireSpecialCharacters: true,
        },
      },
    },
  });
};

export default configureAmplify;
