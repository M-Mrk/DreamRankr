/**
 * Toggles the visibility of an expand row for a specific player
 * Closes all other expanded rows before showing the selected one
 * @param {string} playerId - The ID of the player whose expand row should be toggled
 */
function toggleExpandRow(playerId) {
  // Find the expand row for this player
  const expandRow = document.getElementById(`expand-${playerId}`);

  if (expandRow) {
    // Close all other expanded rows first
    document.querySelectorAll(".expand-row").forEach((row) => {
      if (row !== expandRow) {
        row.style.display = "none";
      }
    });

    // Toggle this row
    if (expandRow.style.display === "none" || expandRow.style.display === "") {
      expandRow.style.display = "table-row";
    } else {
      expandRow.style.display = "none";
    }
  }
}

/**
 * Initializes the challenge system functionality for the trainer page
 * Sets up event handlers for challenge buttons, input validation, and form submission
 * Manages eligible player selection based on ranking system
 */
function initializeChallengeSystem() {
  const challengeModal = document.getElementById("challengeWindow");
  const challengeInput = document.getElementById("input-datalist");
  const challengeDatalist = document.getElementById("list-defender");
  const challengeLabel = document.getElementById("challengeWindowInputLabel");

  // Check if elements exist (only on trainer page)
  if (
    !challengeModal ||
    !challengeInput ||
    !challengeDatalist ||
    !challengeLabel
  ) {
    return;
  }

  // Get or create hidden input fields for challenger and defender IDs
  let challengerIdInput = document.getElementById("challenger-id");
  let defenderIdInput = document.getElementById("defender-id");

  if (!challengerIdInput) {
    challengerIdInput = document.createElement("input");
    challengerIdInput.type = "hidden";
    challengerIdInput.id = "challenger-id";
    challengerIdInput.name = "challenger_id";
    challengeModal.querySelector("form").appendChild(challengerIdInput);
  }

  if (!defenderIdInput) {
    defenderIdInput = document.createElement("input");
    defenderIdInput.type = "hidden";
    defenderIdInput.id = "defender-id";
    defenderIdInput.name = "defender_id";
    challengeModal.querySelector("form").appendChild(defenderIdInput);
  }

  // Extract player data from DOM elements for processing
  const playerRows = document.querySelectorAll(".player-row");
  const allPlayers = Array.from(playerRows).map((row) => {
    // Get the ranking from the first cell of the row
    const rankingCell = row.querySelector("td:first-child strong");
    const ranking = rankingCell ? parseInt(rankingCell.textContent) : 0;

    return {
      id: row.getAttribute("data-player-id"),
      name: row.getAttribute("data-player-name"),
      ranking: ranking,
    };
  });

  // Attach event handlers to all challenge buttons
  document.querySelectorAll(".challenge-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const playerName = this.getAttribute("data-player-name");
      const playerId = this.getAttribute("data-player-id");

      // Find the player's ranking information
      const currentPlayer = allPlayers.find((p) => p.name === playerName);
      if (!currentPlayer) return;

      // Update modal interface with challenger information
      challengeLabel.textContent = playerName + " challenges who?";

      // Reset modal input state
      challengeDatalist.innerHTML = "";
      challengeInput.value = "";
      challengeInput.disabled = false;
      challengeInput.placeholder = "Choose a player...";

      // Store challenger ID for form submission
      challengerIdInput.value = playerId;

      // Handle case where player is already rank 1 (highest ranking)
      if (currentPlayer.ranking === 1) {
        challengeInput.placeholder = "Is already the best!";
        challengeInput.disabled = true;
        challengeModal.setAttribute("data-challenger-id", "");
        challengeModal.setAttribute("data-challenger-name", "");
        return;
      }

      // Populate dropdown with players of higher ranking (lower ranking number)
      const eligiblePlayers = allPlayers.filter(
        (p) => p.ranking < currentPlayer.ranking
      );

      eligiblePlayers.forEach((player) => {
        const option = document.createElement("option");
        option.value = player.name;
        option.setAttribute("data-player-id", player.id);
        challengeDatalist.appendChild(option);
      });

      // Store challenger information for later reference
      challengeModal.setAttribute("data-challenger-id", playerId);
      challengeModal.setAttribute("data-challenger-name", playerName);
    });
  });

  // Validate input selection and update defender ID field
  challengeInput.addEventListener("input", function () {
    if (this.disabled) return;

    const currentValue = this.value;
    const options = Array.from(challengeDatalist.options);
    const validOption = options.find((option) => option.value === currentValue);

    if (currentValue && !validOption) {
      this.setCustomValidity("Please select a valid player from the list");
      defenderIdInput.value = "";
    } else {
      this.setCustomValidity("");
      if (validOption) {
        // Set defender ID based on selected player
        const defenderId =
          validOption.getAttribute("data-player-id") ||
          allPlayers.find((p) => p.name === currentValue)?.id ||
          "";
        defenderIdInput.value = defenderId;
      } else {
        defenderIdInput.value = "";
      }
    }
  });

  // Handle challenge form submission via start button
  const startButton = challengeModal.querySelector(".btn-primary");
  const challengeForm = challengeModal.querySelector("form");

  if (startButton && challengeForm) {
    startButton.addEventListener("click", function (e) {
      e.preventDefault(); // Prevent default button behavior

      // Validate that player can be challenged
      if (challengeInput.disabled) {
        alert("This player is already the best and cannot be challenged!");
        return;
      }

      const challengedPlayer = challengeInput.value;
      const challengerId = challengerIdInput.value;
      const defenderId = defenderIdInput.value;

      if (!challengedPlayer || !challengerId || !defenderId) {
        alert("Please select a player to challenge");
        return;
      }

      // Submit the form with validated data
      challengeForm.submit();
    });
  }
}

/**
 * Initializes the finish match modal functionality
 * Manages mutual exclusivity between input fields and checkboxes
 * Prevents browser autocomplete and resets modal state on show
 */
function initializeFinishMatchModal() {
  const challengerSetsInput = document.getElementById("inputChallengerSetsWon");
  const defenderSetsInput = document.getElementById("inputDefenderSetsWon");
  const challengerWonCheckbox = document.getElementById(
    "challengerWonCheckbox"
  );
  const defenderWonCheckbox = document.getElementById("defenderWonCheckbox");
  const matchIdInput = document.getElementById("match-id");
  const winnerIdInput = document.getElementById("winner-id");

  if (
    !challengerSetsInput ||
    !defenderSetsInput ||
    !challengerWonCheckbox ||
    !defenderWonCheckbox ||
    !matchIdInput ||
    !winnerIdInput
  ) {
    return;
  }

  // Store challenger and defender IDs for winner determination
  let challengerId = "";
  let defenderId = "";

  // Disable browser autocomplete to prevent saved value interference
  challengerSetsInput.setAttribute("autocomplete", "off");
  defenderSetsInput.setAttribute("autocomplete", "off");

  /**
   * Updates the winner_id based on checkbox selections
   */
  function updateWinnerId() {
    if (challengerWonCheckbox.checked) {
      winnerIdInput.value = challengerId;
    } else if (defenderWonCheckbox.checked) {
      winnerIdInput.value = defenderId;
    } else {
      // Clear winner_id if no checkbox is selected (sets will determine winner)
      winnerIdInput.value = "";
    }
  }

  /**
   * Disables and clears checkboxes when input fields contain values
   */
  function updateCheckboxStates() {
    const challengerSets = challengerSetsInput.value.trim();
    const defenderSets = defenderSetsInput.value.trim();

    // Disable checkboxes if any input has a value
    const hasInputValues = challengerSets !== "" || defenderSets !== "";

    challengerWonCheckbox.disabled = hasInputValues;
    defenderWonCheckbox.disabled = hasInputValues;

    // Clear checkboxes if inputs have values
    if (hasInputValues) {
      challengerWonCheckbox.checked = false;
      defenderWonCheckbox.checked = false;
      updateWinnerId(); // Clear winner_id when using sets
    }
  }

  /**
   * Disables and clears input fields when checkboxes are selected
   */
  function updateInputStates() {
    const challengerChecked = challengerWonCheckbox.checked;
    const defenderChecked = defenderWonCheckbox.checked;

    // Disable inputs if any checkbox is checked
    const hasCheckedBoxes = challengerChecked || defenderChecked;

    challengerSetsInput.disabled = hasCheckedBoxes;
    defenderSetsInput.disabled = hasCheckedBoxes;

    // Clear inputs if checkboxes are checked
    if (hasCheckedBoxes) {
      challengerSetsInput.value = "";
      defenderSetsInput.value = "";
    }

    updateWinnerId(); // Update winner_id based on checkbox selection
  }

  /**
   * Ensures only one checkbox can be selected at a time
   * @param {HTMLElement} clickedCheckbox - The checkbox that was clicked
   * @param {HTMLElement} otherCheckbox - The other checkbox to deselect
   */
  function handleCheckboxExclusivity(clickedCheckbox, otherCheckbox) {
    if (clickedCheckbox.checked) {
      otherCheckbox.checked = false;
    }
  }

  // Monitor input field changes to update checkbox states
  challengerSetsInput.addEventListener("input", updateCheckboxStates);
  defenderSetsInput.addEventListener("input", updateCheckboxStates);

  // Monitor checkbox changes with mutual exclusivity enforcement
  challengerWonCheckbox.addEventListener("change", function () {
    handleCheckboxExclusivity(this, defenderWonCheckbox);
    updateInputStates();
  });

  defenderWonCheckbox.addEventListener("change", function () {
    handleCheckboxExclusivity(this, challengerWonCheckbox);
    updateInputStates();
  });

  // Reset all modal fields and states when modal is opened
  const finishMatchModal = document.getElementById("finishMatchModal");
  if (finishMatchModal) {
    finishMatchModal.addEventListener("show.bs.modal", function (event) {
      // Get the button that triggered the modal
      const button = event.relatedTarget;

      // Reset form fields
      challengerSetsInput.value = "";
      defenderSetsInput.value = "";
      challengerWonCheckbox.checked = false;
      defenderWonCheckbox.checked = false;
      challengerSetsInput.disabled = false;
      defenderSetsInput.disabled = false;
      challengerWonCheckbox.disabled = false;
      defenderWonCheckbox.disabled = false;
      winnerIdInput.value = ""; // Reset winner_id

      // Set the match ID from the button's data attribute
      if (button && button.hasAttribute("data-match-id")) {
        matchIdInput.value = button.getAttribute("data-match-id");
      }

      // Store challenger and defender IDs for winner determination
      challengerId = button
        ? button.getAttribute("data-challenger-id") || ""
        : "";
      defenderId = button ? button.getAttribute("data-defender-id") || "" : "";

      // Update modal labels with player names if available
      const challengerName = button
        ? button.getAttribute("data-challenger-name")
        : "";
      const defenderName = button
        ? button.getAttribute("data-defender-name")
        : "";

      if (challengerName && defenderName) {
        const challengerLabel = document.querySelector(
          'label[for="inputChallengerSetsWon"]'
        );
        const defenderLabel = document.querySelector(
          'label[for="inputDefenderSetsWon"]'
        );
        const challengerCheckboxLabel = document.querySelector(
          'label[for="challengerWonCheckbox"]'
        );
        const defenderCheckboxLabel = document.querySelector(
          'label[for="defenderWonCheckbox"]'
        );

        if (challengerLabel) challengerLabel.textContent = challengerName;
        if (defenderLabel) defenderLabel.textContent = defenderName;
        if (challengerCheckboxLabel)
          challengerCheckboxLabel.textContent = `${challengerName} Won`;
        if (defenderCheckboxLabel)
          defenderCheckboxLabel.textContent = `${defenderName} Won`;
      }
    });

    // Handle finish match form submission
    const finishMatchButton = finishMatchModal.querySelector(
      ".modal-footer .btn-primary"
    );
    const finishMatchForm = finishMatchModal.querySelector("form");

    if (finishMatchButton && finishMatchForm) {
      finishMatchButton.addEventListener("click", function (e) {
        e.preventDefault(); // Prevent default button behavior

        // Validate that either sets are filled or a checkbox is selected
        const challengerSets = challengerSetsInput.value.trim();
        const defenderSets = defenderSetsInput.value.trim();
        const challengerWon = challengerWonCheckbox.checked;
        const defenderWon = defenderWonCheckbox.checked;

        const hasSets = challengerSets !== "" && defenderSets !== "";
        const hasWinner = challengerWon || defenderWon;

        if (!hasSets && !hasWinner) {
          alert(
            "Please either enter the sets won by each player or select a winner."
          );
          return;
        }

        if (hasSets && hasWinner) {
          alert("Please use either set scores OR winner selection, not both.");
          return;
        }

        // Submit the form first
        finishMatchForm.submit();

      });
    }
  }
}

/**
 * Initializes the edit player modal functionality
 * Populates form fields with current player data and handles form submission
 */
function initializeEditPlayerModal() {
  const editModal = document.getElementById("editPlayerModal");
  const editForm = document.getElementById("editPlayerForm");
  const saveBtn = document.getElementById("savePlayerBtn");
  const deleteBtn = document.getElementById("deletePlayerBtn");
  const deleteConfirmationModal = document.getElementById(
    "deleteConfirmationModal"
  );
  const confirmDeleteBtn = document.getElementById("confirmDeletePlayer");
  const deletePlayerNameConfirm = document.getElementById(
    "deletePlayerNameConfirm"
  );

  // Get toggle elements
  const changeRankingToggle = document.getElementById("changeRankingToggle");
  const changeWinsLossesToggle = document.getElementById(
    "changeWinsLossesToggle"
  );
  const changeSetsToggle = document.getElementById("changeSetsToggle");

  const rankingSection = document.getElementById("rankingSection");
  const winsLossesSection = document.getElementById("winsLossesSection");
  const setsSection = document.getElementById("setsSection");

  if (!editModal || !editForm || !saveBtn || !deleteBtn) {
    return; // Not on trainer page
  }

  // Handle toggle switches
  if (changeRankingToggle && rankingSection) {
    changeRankingToggle.addEventListener("change", function () {
      if (this.checked) {
        rankingSection.style.display = "block";
        document.getElementById("editPlayerRanking").required = true;
      } else {
        rankingSection.style.display = "none";
        document.getElementById("editPlayerRanking").required = false;
        document.getElementById("editPlayerRanking").value = "";
      }
    });
  }

  if (changeWinsLossesToggle && winsLossesSection) {
    changeWinsLossesToggle.addEventListener("change", function () {
      if (this.checked) {
        winsLossesSection.style.display = "block";
        document.getElementById("editPlayerWins").required = true;
        document.getElementById("editPlayerLosses").required = true;
      } else {
        winsLossesSection.style.display = "none";
        document.getElementById("editPlayerWins").required = false;
        document.getElementById("editPlayerLosses").required = false;
        document.getElementById("editPlayerWins").value = "";
        document.getElementById("editPlayerLosses").value = "";
      }
    });
  }

  if (changeSetsToggle && setsSection) {
    changeSetsToggle.addEventListener("change", function () {
      if (this.checked) {
        setsSection.style.display = "block";
        document.getElementById("editPlayerSetsWon").required = true;
        document.getElementById("editPlayerSetsLost").required = true;
      } else {
        setsSection.style.display = "none";
        document.getElementById("editPlayerSetsWon").required = false;
        document.getElementById("editPlayerSetsLost").required = false;
        document.getElementById("editPlayerSetsWon").value = "";
        document.getElementById("editPlayerSetsLost").value = "";
      }
    });
  }

  // Populate modal when it's opened
  editModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget;

    if (button) {
      // Get player data from button attributes
      const playerId = button.getAttribute("data-player-id");
      const playerName = button.getAttribute("data-player-name");
      const playerRanking = button.getAttribute("data-player-ranking");
      const playerWins = button.getAttribute("data-player-wins");
      const playerLosses = button.getAttribute("data-player-losses");
      const playerSetsWon = button.getAttribute("data-player-sets-won");
      const playerSetsLost = button.getAttribute("data-player-sets-lost");

      // Populate form fields
      document.getElementById("editPlayerId").value = playerId;
      document.getElementById("editPlayerName").value = playerName;
      document.getElementById("editPlayerRanking").value = playerRanking;
      document.getElementById("editPlayerWins").value = playerWins;
      document.getElementById("editPlayerLosses").value = playerLosses;
      document.getElementById("editPlayerSetsWon").value = playerSetsWon;
      document.getElementById("editPlayerSetsLost").value = playerSetsLost;

      // Update modal title
      document.getElementById(
        "editPlayerModalLabel"
      ).textContent = `Edit ${playerName}`;

      // Reset toggles and hide sections
      changeRankingToggle.checked = false;
      changeWinsLossesToggle.checked = false;
      changeSetsToggle.checked = false;

      rankingSection.style.display = "none";
      winsLossesSection.style.display = "none";
      setsSection.style.display = "none";

      // Remove required attributes when sections are hidden
      document.getElementById("editPlayerRanking").required = false;
      document.getElementById("editPlayerWins").required = false;
      document.getElementById("editPlayerLosses").required = false;
      document.getElementById("editPlayerSetsWon").required = false;
      document.getElementById("editPlayerSetsLost").required = false;
    }
  });

  // Handle save button click
  saveBtn.addEventListener("click", function (e) {
    e.preventDefault();

    // Only validate visible/enabled fields
    const visibleInputs = editForm.querySelectorAll(
      'input:not([type="hidden"]):not([style*="display: none"]) input[required]'
    );
    let isValid = true;

    // Custom validation for visible required fields
    visibleInputs.forEach((input) => {
      if (input.required && !input.value.trim()) {
        isValid = false;
        input.reportValidity();
      }
    });

    if (!isValid) {
      return;
    }

    // Submit form
    editForm.submit();
  });

  // Handle delete button click - show confirmation modal
  deleteBtn.addEventListener("click", function (e) {
    e.preventDefault();

    const playerName = document.getElementById("editPlayerName").value;
    const playerId = document.getElementById("editPlayerId").value;

    // Update confirmation modal with player info
    deletePlayerNameConfirm.textContent = playerName;

    // Store player ID for the actual deletion
    confirmDeleteBtn.setAttribute("data-player-id", playerId);
    confirmDeleteBtn.setAttribute("data-player-name", playerName);

    // Hide the edit modal and show confirmation modal
    const editModalInstance = bootstrap.Modal.getInstance(editModal);
    editModalInstance.hide();

    // Show confirmation modal after edit modal is hidden
    editModal.addEventListener("hidden.bs.modal", function showDeleteModal() {
      const deleteModalInstance = new bootstrap.Modal(deleteConfirmationModal);
      deleteModalInstance.show();
      // Remove the event listener to prevent multiple attachments
      editModal.removeEventListener("hidden.bs.modal", showDeleteModal);
    });
  });

  // Handle actual deletion when confirmed
  if (confirmDeleteBtn && deleteConfirmationModal) {
    confirmDeleteBtn.addEventListener("click", function (e) {
      e.preventDefault();

      const playerId = this.getAttribute("data-player-id");
      const playerName = this.getAttribute("data-player-name");

      if (playerId) {
        // Create a form for deletion
        const deleteForm = document.createElement("form");
        deleteForm.method = "post";
        deleteForm.action = "/trainer/player_delete";

        const playerIdInput = document.createElement("input");
        playerIdInput.type = "hidden";
        playerIdInput.name = "player_id";
        playerIdInput.value = playerId;

        deleteForm.appendChild(playerIdInput);
        document.body.appendChild(deleteForm);

        // Hide the confirmation modal
        const deleteModalInstance = bootstrap.Modal.getInstance(
          deleteConfirmationModal
        );
        deleteModalInstance.hide();

        // Submit the form
        deleteForm.submit();
      }
    });

    // Clean up when delete confirmation modal is hidden
    deleteConfirmationModal.addEventListener("hidden.bs.modal", function () {
      confirmDeleteBtn.removeAttribute("data-player-id");
      confirmDeleteBtn.removeAttribute("data-player-name");
      deletePlayerNameConfirm.textContent = "";
    });
  }

  // Reset form when edit modal is hidden
  editModal.addEventListener("hidden.bs.modal", function () {
    editForm.reset();
    // Reset toggles
    changeRankingToggle.checked = false;
    changeWinsLossesToggle.checked = false;
    changeSetsToggle.checked = false;

    // Hide sections
    rankingSection.style.display = "none";
    winsLossesSection.style.display = "none";
    setsSection.style.display = "none";
  });
}

/**
 * Replaces modal content with a loading spinner
 * @param {string} id - The ID of the element to replace with spinner
 */
function startSpinner(id) {
  const modal = document.getElementById(id);
  modal.textContent = "";
  modal.innerHTML =
    '<div class="d-flex justify-content-center"> <div class="spinner-border" role="status"> <span class="visually-hidden">Loading...</span> </div> </div>';
}

/**
 * Initialize active matches settings with Bootstrap Offcanvas
 */
function initializeActiveMatchesSettings() {
  const offcanvas = document.getElementById("activeMatchesSettings");
  const displayMode = document.getElementById("displayMode");
  const showElapsed = document.getElementById("showElapsed");
  const autoRefresh = document.getElementById("autoRefresh");
  const applyBtn = document.getElementById("applySettings");

  if (!offcanvas) return; // Not on trainer page

  // Load saved settings
  const settings = JSON.parse(
    localStorage.getItem("activeMatchesSettings") ||
      '{"displayMode":"carousel","showElapsed":false,"autoRefresh":false}'
  );

  // Apply saved settings to form
  displayMode.value = settings.displayMode;
  showElapsed.checked = settings.showElapsed;
  autoRefresh.checked = settings.autoRefresh;

  // Apply current settings to display
  applyDisplaySettings(settings);

  // Save and apply when button clicked
  applyBtn.addEventListener("click", () => {
    const newSettings = {
      displayMode: displayMode.value,
      showElapsed: showElapsed.checked,
      autoRefresh: autoRefresh.checked,
    };

    localStorage.setItem("activeMatchesSettings", JSON.stringify(newSettings));
    applyDisplaySettings(newSettings);

    // Close offcanvas
    bootstrap.Offcanvas.getInstance(offcanvas).hide();

    // Show toast notification
    showToast("Settings applied successfully!", "success");
  });
}

/**
 * Apply display settings to active matches
 */
function applyDisplaySettings(settings) {
  const container = document.querySelector(".activeMatches");
  if (!container) return;

  container.className = "activeMatches";
  container.classList.add(`display-${settings.displayMode}`);

  const carousel = container.querySelector("#activeMatchesCarousel");
  if (carousel) {
    const carouselInstance = bootstrap.Carousel.getInstance(carousel);

    if (settings.displayMode !== "carousel") {
      // Dispose carousel and show all items
      carouselInstance?.dispose();
      carousel.querySelectorAll(".carousel-item").forEach((item) => {
        item.classList.add("active");
      });
    } else {
      // Reset and reinitialize carousel
      carousel.querySelectorAll(".carousel-item").forEach((item, index) => {
        item.classList.toggle("active", index === 0);
      });

      // Only create if not already exists
      if (!carouselInstance) {
        new bootstrap.Carousel(carousel, { interval: false, wrap: true });
      }
    }
  }

  // Handle other settings
  if (settings.showElapsed) updateTimeDisplay(true);
  settings.autoRefresh ? startAutoRefresh() : stopAutoRefresh();
}

/**
 * Update time display between elapsed and start time
 */
function updateTimeDisplay(showElapsed) {
  const timeElements = document.querySelectorAll(".activeMatches .text-muted");
  timeElements.forEach((el) => {
    const startTimestamp = el.getAttribute("data-start-timestamp");

    if (showElapsed && el.textContent.includes("Since:") && startTimestamp) {
      const elapsed = calculateElapsedFromTimestamp(parseFloat(startTimestamp));
      const originalText = el.textContent;
      el.textContent = `Elapsed: ${elapsed}`;
      // Store original text for restoration
      el.setAttribute("data-original-text", originalText);
    } else if (!showElapsed && el.textContent.includes("Elapsed:")) {
      // Restore original text if available
      const originalText = el.getAttribute("data-original-text");
      if (originalText) {
        el.textContent = originalText;
      } else {
        // Fallback - reconstruct from timestamp
        if (startTimestamp) {
          const startDate = new Date(parseFloat(startTimestamp) * 1000);
          const timeStr = startDate.toLocaleTimeString("en-GB", {
            hour: "2-digit",
            minute: "2-digit",
          });
          el.textContent = `Since: ${timeStr}`;
        }
      }
    }
  });
}

/**
 * Calculate elapsed time from Unix timestamp (UTC)
 * @param {number} startTimestamp - Unix timestamp in seconds (UTC)
 * @returns {string} Formatted elapsed time string
 */
function calculateElapsedFromTimestamp(startTimestamp) {
  const now = new Date();
  const start = new Date(startTimestamp * 1000); // Convert to milliseconds

  // Adjust the start time to the local timezone
  const timezoneOffsetMs = now.getTimezoneOffset() * 60000; // Convert minutes to milliseconds
  const localStart = new Date(start.getTime() - timezoneOffsetMs);

  // Calculate the difference in milliseconds
  const diffMs = now - localStart;
  const diffMins = Math.floor(diffMs / 60000);

  // Ensure we don't show negative times
  if (diffMins < 0) {
    return "0m";
  }

  if (diffMins < 60) {
    return `${diffMins}m`;
  }

  const hours = Math.floor(diffMins / 60);
  const remainingMins = diffMins % 60;

  return `${hours}h ${remainingMins}m`;
}

/**
 * Start auto-refresh interval
 */
function startAutoRefresh() {
  stopAutoRefresh(); // Clear existing
  window.matchesRefreshInterval = setInterval(() => {
    const settings = JSON.parse(
      localStorage.getItem("activeMatchesSettings") || "{}"
    );
    if (settings.showElapsed) updateTimeDisplay(true);
  }, 30000);
}

/**
 * Stop auto-refresh interval
 */
function stopAutoRefresh() {
  if (window.matchesRefreshInterval) {
    clearInterval(window.matchesRefreshInterval);
    window.matchesRefreshInterval = null;
  }
}

/**
 * Show Bootstrap toast notification - simplified version
 */
function showToast(message, type = "primary") {
  // Create toast container if it doesn't exist
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container position-fixed top-0 end-0 p-3";
    document.body.appendChild(container);
  }

  // Create and show toast
  const toast = document.createElement("div");
  toast.className = `toast align-items-center text-white bg-${type}`;
  toast.setAttribute("role", "alert");
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;

  container.appendChild(toast);
  const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
  bsToast.show();

  toast.addEventListener("hidden.bs.toast", () => toast.remove());
}

// Initialize all functionality when DOM is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  // Set up click handlers for player table rows
  const playerRows = document.querySelectorAll(".player-row");
  playerRows.forEach((row) => {
    row.addEventListener("click", function () {
      const playerId = this.getAttribute("data-player-id");
      toggleExpandRow(playerId);
    });
    row.style.cursor = "pointer";
  });

  // Initialize all functionality
  initializeChallengeSystem();
  initializeFinishMatchModal();
  initializeActiveMatchesSettings();
  initializeEditPlayerModal(); // Add this line

  // Initialize Bootstrap tooltips if any exist
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
