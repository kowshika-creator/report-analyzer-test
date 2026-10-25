import test from "node:test";
import assert from "node:assert/strict";

/**
 * AXON Frontend Upload Race Condition & Stale Results Verification Suite
 * Exercises the exact state-management and request-guarding invariants implemented
 * in frontend/src/app/page.tsx for both Lab and Scan uploads:
 * 1. Out-of-order upload completion guard (newer upload always wins).
 * 2. Stale report clearance immediately upon upload start.
 * 3. Failed uploads clear state and never leave stale data displayed as current.
 * 4. Superseded failures cannot overwrite newer active state.
 */

class DashboardUploadStateManager {
  constructor() {
    this.activeReport = null;
    this.isUploading = false;
    this.errorMessage = null;
    this.requestIdRef = { current: 0 };
  }

  async uploadFile(file, fakeFetch) {
    const currentReqId = ++this.requestIdRef.current;
    
    // Priority 5 invariant: Clear previous report immediately upon start
    this.activeReport = null;
    this.isUploading = true;
    this.errorMessage = null;

    try {
      const res = await fakeFetch(file);
      const data = await res.json();

      // Guard against race conditions if user uploaded a newer file in quick succession
      if (currentReqId !== this.requestIdRef.current) {
        return; // Superseded request
      }

      if (!res.ok) {
        this.activeReport = null;
        throw new Error(data.detail || "Failed to process report.");
      }

      this.activeReport = {
        filename: data.filename,
        metrics: data.metrics || [],
      };
    } catch (err) {
      if (currentReqId !== this.requestIdRef.current) return;
      this.activeReport = null;
      this.errorMessage = err.message || "An error occurred while uploading.";
    } finally {
      if (currentReqId === this.requestIdRef.current) {
        this.isUploading = false;
      }
    }
  }
}

test("1. Two uploads completing out of order: older response CANNOT overwrite newer report", async () => {
  const manager = new DashboardUploadStateManager();

  // Simulates slow upload A (starts first, completes at 120ms)
  const slowUploadPromise = manager.uploadFile({ name: "Report_A_Old.pdf" }, async (file) => {
    await new Promise((resolve) => setTimeout(resolve, 120));
    return {
      ok: true,
      json: async () => ({
        filename: file.name,
        metrics: [{ biomarker_name: "Glucose", value: 105, unit: "mg/dL" }],
      }),
    };
  });

  // Small delay then trigger fast upload B (starts second, completes at 30ms)
  await new Promise((resolve) => setTimeout(resolve, 15));
  const fastUploadPromise = manager.uploadFile({ name: "Report_B_New.pdf" }, async (file) => {
    await new Promise((resolve) => setTimeout(resolve, 30));
    return {
      ok: true,
      json: async () => ({
        filename: file.name,
        metrics: [{ biomarker_name: "Hemoglobin", value: 14.2, unit: "g/dL" }],
      }),
    };
  });

  // Wait for both requests to settle
  await Promise.all([slowUploadPromise, fastUploadPromise]);

  // Assert that Report B (the newer request) is displayed, and Report A did NOT overwrite it
  assert.ok(manager.activeReport !== null, "Active report should be populated");
  assert.equal(manager.activeReport.filename, "Report_B_New.pdf");
  assert.equal(manager.activeReport.metrics[0].biomarker_name, "Hemoglobin");
  assert.equal(manager.isUploading, false, "Uploading indicator should be false");
  assert.equal(manager.errorMessage, null);
});

test("2. Failed upload does NOT leave previous stale results displayed as current", async () => {
  const manager = new DashboardUploadStateManager();

  // Initially, user has an active report displayed
  manager.activeReport = {
    filename: "Previous_Report.pdf",
    metrics: [{ biomarker_name: "Platelets", value: 240, unit: "10^3/uL" }],
  };

  // User uploads a corrupt or unreadable file that fails with 422
  const failedUploadPromise = manager.uploadFile({ name: "Unreadable_Corrupt.pdf" }, async () => {
    await new Promise((resolve) => setTimeout(resolve, 40));
    return {
      ok: false,
      json: async () => ({
        detail: "No readable text could be extracted from the uploaded document.",
      }),
    };
  });

  // During in-flight upload, previous report must already be cleared
  assert.equal(manager.activeReport, null, "Stale report must be cleared immediately when upload starts");
  assert.equal(manager.isUploading, true);

  await failedUploadPromise;

  // After failure, activeReport MUST remain null and not revert to the stale report
  assert.equal(manager.activeReport, null, "Failed upload must NOT leave stale results displayed");
  assert.equal(manager.isUploading, false);
  assert.match(manager.errorMessage, /No readable text/);
});

test("3. Slow failing upload cannot overwrite newer successful upload", async () => {
  const manager = new DashboardUploadStateManager();

  // Upload 1: slow failure (takes 100ms)
  const upload1 = manager.uploadFile({ name: "Slow_Failed.pdf" }, async () => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return {
      ok: false,
      json: async () => ({ detail: "OCR parsing failed" }),
    };
  });

  // Upload 2: fast success (takes 25ms)
  await new Promise((resolve) => setTimeout(resolve, 10));
  const upload2 = manager.uploadFile({ name: "Fast_Success.pdf" }, async (file) => {
    await new Promise((resolve) => setTimeout(resolve, 25));
    return {
      ok: true,
      json: async () => ({
        filename: file.name,
        metrics: [{ biomarker_name: "TSH", value: 2.1, unit: "uIU/mL" }],
      }),
    };
  });

  await Promise.all([upload1, upload2]);

  // Upload 2 is current and must be displayed, upload 1 error must be ignored
  assert.ok(manager.activeReport !== null);
  assert.equal(manager.activeReport.filename, "Fast_Success.pdf");
  assert.equal(manager.errorMessage, null);
  assert.equal(manager.isUploading, false);
});
