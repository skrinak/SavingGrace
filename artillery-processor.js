/**
 * Artillery Processor Functions
 * Custom functions for generating test data and authentication
 */

/**
 * Authenticate user before scenario
 */
function authenticateUser(context, events, done) {
  // In a real scenario, you would call the auth endpoint here
  // For now, we'll use a test token
  context.vars.accessToken = process.env.TEST_ACCESS_TOKEN || 'test-token';

  // Generate test IDs
  context.vars.donorId = generateUUID();
  context.vars.recipientId = generateUUID();

  // Generate dates
  const today = new Date();
  context.vars.todayDate = today.toISOString().split('T')[0];

  const futureDate = new Date();
  futureDate.setDate(futureDate.getDate() + 7);
  context.vars.futureDate = futureDate.toISOString().split('T')[0];

  const startDate = new Date();
  startDate.setMonth(startDate.getMonth() - 1);
  context.vars.startDate = startDate.toISOString().split('T')[0];
  context.vars.endDate = today.toISOString().split('T')[0];

  return done();
}

/**
 * Generate UUID v4
 */
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Log response time for monitoring
 */
function logResponseTime(requestParams, response, context, ee, next) {
  if (response.timings) {
    console.log(`Response time: ${response.timings.phases.total}ms`);
  }
  return next();
}

/**
 * Handle authentication errors
 */
function handleAuthError(requestParams, response, context, ee, next) {
  if (response.statusCode === 401) {
    console.log('Authentication failed, refreshing token...');
    // In real scenario, refresh token logic would go here
  }
  return next();
}

module.exports = {
  authenticateUser,
  logResponseTime,
  handleAuthError,
};
