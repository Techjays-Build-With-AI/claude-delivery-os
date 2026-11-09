/* ============================================================
 * DELIBERATELY VULNERABLE - REVIEW RECALL FIXTURE, NOT REAL CODE
 *
 * Every defect in this file is planted on purpose and catalogued in
 * ../ANSWER-KEY.md. It exists to measure whether a reviewer finds them.
 * DO NOT FIX. DO NOT COPY. DO NOT SHIP. Fixing it destroys the only
 * recall measurement Delivery OS has.
 * ============================================================ */
'use strict';

// RF-03 (matches-existing-pattern): no null guard on input - exactly like the
//        handlers around it, which is what makes it invisible to a reviewer
//        told to match the repo's conventions.
// RF-02 (cross-file, caller half): userId may be undefined here.

const { findUserOrders, profileFor } = require('./store');

function getOrders(req, db) {
  return findUserOrders(db, req.query.userId);
}

function getProfile(req, users) {
  return profileFor(users, req.query.userId);
}

function getSettings(req, settings) {
  return settings[req.query.userId];
}

module.exports = { getOrders, getProfile, getSettings };
