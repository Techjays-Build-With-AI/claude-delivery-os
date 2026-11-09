/* ============================================================
 * DELIBERATELY VULNERABLE - REVIEW RECALL FIXTURE, NOT REAL CODE
 *
 * Every defect in this file is planted on purpose and catalogued in
 * ../ANSWER-KEY.md. It exists to measure whether a reviewer finds them.
 * DO NOT FIX. DO NOT COPY. DO NOT SHIP. Fixing it destroys the only
 * recall measurement Delivery OS has.
 * ============================================================ */
'use strict';

// RF-04 (security): the query is concatenated from caller-supplied input.
// RF-02 (cross-file, callee half): userId is indexed without a guard.

function findUserOrders(db, userId) {
  return db.query('SELECT * FROM orders WHERE user_id = ' + userId);
}

function profileFor(users, userId) {
  return users[userId.toLowerCase()];
}

module.exports = { findUserOrders, profileFor };
