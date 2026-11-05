/* ============================================================
 * DELIBERATELY VULNERABLE - REVIEW RECALL FIXTURE, NOT REAL CODE
 *
 * Every defect in this file is planted on purpose and catalogued in
 * ../ANSWER-KEY.md. It exists to measure whether a reviewer finds them.
 * DO NOT FIX. DO NOT COPY. DO NOT SHIP. Fixing it destroys the only
 * recall measurement Delivery OS has.
 * ============================================================ */
'use strict';

// RF-01 (absence): isExpired is defined and never called before access is granted.
// RF-05 (business-rule): BR-1 says one active session per user. Nothing enforces it.

const sessions = new Map();

function isExpired(session) {
  return Date.now() > session.expiresAt;
}

function createSession(userId, ttlMs) {
  const session = { userId, expiresAt: Date.now() + ttlMs, token: String(Math.random()) };
  sessions.set(session.token, session);
  return session;
}

function resolveSession(token) {
  const session = sessions.get(token);
  if (!session) return null;
  return session;
}

module.exports = { createSession, resolveSession, isExpired };
