import { useState } from "react";
import "./App.css";
import SubAccountConfirmation from "./components/subAccountConfirmation";

function App() {
  const [memberId, setMemberId] = useState("");
  const [member, setMember] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showBalances, setShowBalances] = useState(true);
  const [showSubAccountModal, setShowSubAccountModal] = useState(false);
  const [subAccount, setSubAccount] = useState(null);
  const [subAccountLoading, setSubAccountLoading] = useState(false);
  const [subAccountError, setSubAccountError] = useState("");
  const [initialDeposit, setInitialDeposit] = useState("");

  const searchMember = async () => {
    const trimmedId = memberId.trim();

    setError("");
    setMember(null);

    if (!trimmedId) {
      setError("Please enter a member ID");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `http://localhost:8001/api/members/${trimmedId}`
      );

      const data = await response.json();

      if (!response.ok) {
        if (response.status >= 500) {
          setError("Service temporarily unavailable");
          return;
        }

        setError("Member not found");
        return;
      }

      if (!data.found) {
        setError("Member not found");
        return;
      }

      setMember(data.member);
    } catch (err) {
      setError("Service temporarily unavailable");
    } finally {
      setLoading(false);
    }
  };

 const approveSubAccount = async () => {
  if (!member) {
    return;
  }

  if (!initialDeposit || Number(initialDeposit) < 0) {
    setSubAccountError(
      "Please enter a valid initial deposit."
    );
    return;
  }

  setSubAccountLoading(true);
  setSubAccountError("");

  try {
    const response = await fetch(
      `http://localhost:8001/api/members/${member.member_id}/sub-accounts`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          account_type: "savings",
          initial_deposit: Number(initialDeposit),
        }),
      }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
      setSubAccountError(
        data.message || "Unable to open sub-account"
      );
      return;
    }

    setSubAccount(data.sub_account);
    setShowSubAccountModal(false);
    setInitialDeposit("");
  } catch (err) {
    setSubAccountError(
      "Service temporarily unavailable"
    );
  } finally {
    setSubAccountLoading(false);
  }
};

  const clearSearch = () => {
    setMemberId("");
    setMember(null);
    setError("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      searchMember();
    }
  };

  const formatCurrency = (amount) => {
    return `$${amount.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const totalBalance = member? member.checking + member.savings: 0;

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="brand">
            <div className="logo">B</div>
            <div>
              <div className="brand-name">
                Bank App
              </div>

            </div>
          </div>

          <div className="header-right">
            <div className="avatar">
              U
            </div>
          </div>

        </div>
      </header>

      {/* =====================================================
          MAIN
          ===================================================== */}

      <main className="main">

        {/* Page Heading */}
        <section className="page-heading">

          <div className="eyebrow">
            BANK OPERATIONS
          </div>

        </section>

        {/* =================================================
            MEMBER SEARCH
            ================================================= */}

        <section className="search-card">
          <div className="search-card-header">
            <div>
              <div className="section-eyebrow">
                MEMBER SEARCH SERVICE
              </div>
            </div>
          </div>

          <div className="search-row">

            <div className="input-group">

              <input
                id="member-id"
                aria-label="Member ID"
                value={memberId}
                onChange={(e) => setMemberId(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter member ID"
                className="input"
              />

            </div>

            <button
              id="search-member"
              onClick={searchMember}
              disabled={loading}
              className="search-button"
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Searching...
                </>
              ) : (
                <>
                  Search Member
                  <span className="button-arrow">
                    →
                  </span>
                </>
              )}
            </button>

            {(member || memberId) && !loading && (
              <button
                onClick={clearSearch}
                className="clear-button"
              >
                Clear
              </button>
            )}

          </div>

          {error === "Member not found" && (
            <div
              id="member-search-error"
              role="alert"
              className="error-box"
            >

              <div className="error-icon">
                !
              </div>

              <div>
                <strong className="error-title">
                  Member not found
                </strong>

                <div className="error-text">
                  We couldn't find a member with that ID.
                  Please verify the member ID and try again.
                </div>
              </div>

            </div>
          )}


          {error === "Service temporarily unavailable" && (
            <div
              id="member-search-network-error"
              role="alert"
              className="warning-box"
            >

              <div className="warning-icon">
                !
              </div>

              <div>
                <strong className="warning-title">
                  Service temporarily unavailable
                </strong>

                <div className="warning-text">
                  The banking service is temporarily unavailable.
                  Please try again in a moment.
                </div>
              </div>

            </div>
          )}


          {error === "Please enter a member ID" && (
            <div
              role="alert"
              className="validation-box"
            >
              Please enter a member ID to continue.
            </div>
          )}

        </section>


        {member && !subAccount && (
          <section
            id="member-details"
            className="dashboard"
          >

            {/* Customer Header */}
            <div className="customer-header">

              <div className="customer-info">

                <div className="customer-avatar">
                  {member.name.charAt(0).toUpperCase()}
                </div>

                <div>

                  <div className="customer-label">
                    MEMBER PROFILE
                  </div>

                  <h2
                    id="member-details-title"
                    className="customer-name"
                  >
                    {member.name}
                  </h2>

                  <div className="member-number">
                    Member ID:{" "}
                    <span id="member-id-value">
                      {member.member_id}
                    </span>
                  </div>

                </div>

              </div>

              <div className="account-status">
                <span className="status-dot"></span>
                Active Member
              </div>

            </div>


            <div className="summary-grid">

              {/* Total Balance */}
              <div className="total-card">

                <div className="card-top">

                  <span className="card-label">
                    TOTAL RELATIONSHIP BALANCE
                  </span>

                  <button
                    onClick={() =>
                      setShowBalances(!showBalances)
                    }
                    className="eye-button"
                    aria-label={
                      showBalances
                        ? "Hide balances"
                        : "Show balances"
                    }
                  >
                    {showBalances ? "◉" : "○"}
                  </button>

                </div>

                <div className="total-amount">
                  {showBalances
                    ? formatCurrency(totalBalance)
                    : "••••••"}
                </div>

                <div className="total-subtext">
                  Across checking and savings
                </div>

              </div>

              {/* Account Status */}
              <div className="info-card">

                <div className="info-icon">
                  ✓
                </div>

                <div>

                  <div className="card-label">
                    ACCOUNT STATUS
                  </div>

                  <div className="info-value">
                    Active
                  </div>

                  <div className="info-subtext">
                    All accounts available
                  </div>

                </div>

              </div>

            </div>


            <div className="accounts-section">

              <div className="accounts-header">

                <h3 className="accounts-title">
                  Your Accounts 
                <span className="accounts-subtitle">
                 - Current account balances
                </span>

                </h3>
              </div>

              <div className="accounts-grid">

                {/* Checking Account */}
                <div className="account-card">

                  <div className="account-header">

                    <div className="account-icon">
                      C
                    </div>

                    <div>

                      <div className="account-name">
                        Checking
                      </div>

                      <div className="account-number">
                        Everyday Banking
                      </div>

                    </div>

                  </div>

                  <div className="account-balance-label">
                    Available balance
                  </div>

                  <div
                    id="checking-balance"
                    aria-label="Checking Balance"
                    className="account-balance"
                  >
                    {showBalances
                      ? formatCurrency(member.checking)
                      : "••••••"}
                  </div>


                </div>

                {/* Savings Account */}
                <div className="account-card">

                  <div className="account-header">

                    <div className="savings-icon">
                      S
                    </div>

                    <div>

                      <div className="account-name">
                        Savings
                      </div>

                      <div className="account-number">
                        Personal Savings
                      </div>

                    </div>

                  </div>

                  <div className="account-balance-label">
                    Available balance
                  </div>

                  {/* IMPORTANT:
                      Keep this ID for deterministic replay.
                  */}
                  <div
                    id="savings-balance"
                    aria-label="Savings Balance"
                    className="account-balance"
                  >
                    {showBalances
                      ? formatCurrency(member.savings)
                      : "••••••"}
                  </div>

                </div>

              </div>

            </div>


            <div className="actions-section">

              <h3 className="actions-title">
                Account Services
              </h3>

              <div className="action-grid">

                {/* Open Sub Account */}
                <button
                  id="open-sub-account"
                  aria-label="Open Sub-Account"
                  onClick={() =>
                    setShowSubAccountModal(true)
                  }
                  className="action-button"
                >

                  <span className="action-icon">
                    +
                  </span>

                  <span>
                    <strong className="action-button-title">
                      Open Sub-Account
                    </strong>

                    <span className="action-button-text">
                      Add another savings account
                    </span>
                  </span>

                  <span className="action-arrow">
                    →
                  </span>

                </button>

                {/* Statements */}
                <button
                  className="action-button"
                  onClick={() =>
                    alert(
                      "Account statements are available in the full banking portal."
                    )
                  }
                >

                  <span className="action-icon">
                    ▤
                  </span>

                  <span>
                    <strong className="action-button-title">
                      View Statements
                    </strong>

                    <span className="action-button-text">
                      Review account statements
                    </span>
                  </span>

                  <span className="action-arrow">
                    →
                  </span>

                </button>

                {/* Transfers */}
                <button
                  className="action-button"
                  data-safety="blocked"
                  onClick={() =>
                    alert(
                      "Transfer services are available in the full banking portal."
                    )
                  }
                >

                  <span className="action-icon">
                    ⇄
                  </span>

                  <span>
                    <strong className="action-button-title">
                      Transfer Funds
                    </strong>

                    <span className="action-button-text">
                      Move money between accounts
                    </span>
                  </span>
                  <span className="action-arrow">
                    →
                  </span>
                </button>
              </div>
            </div>
          </section>
        )}

        {member && subAccount && (
          <SubAccountConfirmation
            subAccount={subAccount}
            onReturn={() => setSubAccount(null)}
          />
        )}

      </main>

      {/* =====================================================
          SUB-ACCOUNT MODAL
          ===================================================== */}

      {showSubAccountModal && (
        <div className="modal-overlay">
          <div className="modal">

            <h2 className="modal-title">
              <div className="modal-icon">+</div>
              Open a Sub-Account
            </h2>

            <p className="modal-text">
              Set up a new savings sub-account for this member.
            </p>

            {/* Member information */}
            <div
              id="sub-account-member-details"
              className="member-details"
              style={{ marginTop: "8px" }}
            >
              <div className="member-detail-row">
                <strong className="member-detail-label">
                  Member
                </strong>

                <span className="member-detail-value">
                  {member.name}
                </span>
              </div>

              <div className="member-detail-row">
                <strong className="member-detail-label">
                  Member ID
                </strong>

                <span
                  id="sub-account-member-id"
                  className="member-detail-value"
                >
                  {member.member_id}
                </span>
              </div>
            </div>

            {/* Initial deposit */}
            <div className="input-group" style={{ marginTop: "18px" }}>
              <label
                htmlFor="initial-deposit"
                className="label"
              >
                Initial Deposit
              </label>

              <input
                id="initial-deposit"
                aria-label="Initial Deposit"
                type="number"
                min="0"
                step="0.01"
                value={initialDeposit}
                onChange={(e) => setInitialDeposit(e.target.value)}
                placeholder="Enter initial deposit"
                className="input"
              />
              <span className="input-help">
                Enter the amount to deposit into the new savings account.
              </span>
            </div>

            {/* Review section */}
            <div
              id="sub-account-review"
              className="member-details"
              style={{ marginTop: "20px" }}
            >
              <div className="member-detail-row">
                <strong className="member-detail-label">
                  Account
                </strong>

                <span className="member-detail-value">
                  Savings Sub-Account
                </span>
              </div>

              <div className="member-detail-row">
                <strong className="member-detail-label">
                  Initial Deposit
                </strong>

                <span
                  id="review-initial-deposit"
                  className="member-detail-value"
                >
                  Review required
                </span>
              </div>
            </div>

            {/* Human approval notice */}
            <div className="modal-notice">
              <strong>
                Human approval required
              </strong>

              <span>
                Review the account details before approving
                this protected banking operation.
              </span>
            </div>

            {subAccountError && (
              <div
                id="sub-account-error"
                className="error-box"
              >
                <strong>{subAccountError}</strong>
              </div>
            )}

            <div className="modal-actions">

              <button
                id="cancel-sub-account"
                onClick={() =>
                  setShowSubAccountModal(false)
                }
                className="modal-button modal-button-secondary"
                disabled={subAccountLoading}
              >
                Cancel
              </button>

              <button
                id="approve-sub-account"
                data-safety="human_required"
                onClick={approveSubAccount}
                className="modal-button"
                disabled={subAccountLoading}
              >
                {subAccountLoading
                  ? "Opening..."
                  : "Approve & Continue"}
              </button>

            </div>

          </div>
        </div>
      )}

    </div>
  );
}

export default App;