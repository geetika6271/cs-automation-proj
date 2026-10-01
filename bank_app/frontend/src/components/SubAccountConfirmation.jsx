import "./subAccount.css"

function SubAccountConfirmation({ subAccount, onReturn }) {
  return (
    <section
      id="sub-account-confirmation"
      className="confirmation-page"
    >
      <div className="confirmation-icon">
        ✓
      </div>

      <div className="confirmation-eyebrow">
        ACCOUNT SERVICES
      </div>

      <h1 className="confirmation-title">
        Sub-account opened successfully
      </h1>

      <p className="confirmation-description">
        Your new savings sub-account is now active.
      </p>

      <div className="confirmation-card">

        <div className="confirmation-row">
          <span>Account Type</span>
          <strong>{subAccount.type}</strong>
        </div>

        <div className="confirmation-row">
          <span>Account Number</span>
          <strong>{subAccount.id}</strong>
        </div>

        <div className="confirmation-row">
          <span>Status</span>
          <strong className="confirmation-status">
            {subAccount.status}
          </strong>
        </div>

        <div className="confirmation-row">
          <span>Current Balance</span>
          <strong>
            ${Number(subAccount.balance).toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </strong>
        </div>

      </div>

      <button
        id="return-to-accounts"
        className="confirmation-button"
        onClick={onReturn}
      >
        Return to Accounts
      </button>
    </section>
  );
}

export default SubAccountConfirmation;