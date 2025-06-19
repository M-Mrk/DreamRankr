/**
 * Opens a modal by setting its display style to block
 * @param {string} modalId - The ID of the modal element to open
 */
function openModal(modalId) {
  modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "block";
  }
}

/**
 * Closes a modal by setting its display style to none
 * @param {string} modalId - The ID of the modal element to close
 */
function closeModal(modalId) {
  modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
  }
}

/**
 * Opens the challenge window modal for a specific player
 * @param {string} playerId - The ID of the player initiating the challenge
 */
function openChallengeWindow(playerId) {
  openModal("challengeWindow");
}

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

      console.log("Challenge:", {
        challenger_id: challengerId,
        defender_id: defenderId,
        challenged_player_name: challengedPlayer,
      });

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
    console.log("Some elements not found for finish match modal");
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

        console.log("Form validation:", {
          hasSets,
          hasWinner,
          challengerSets,
          defenderSets,
          challengerWon,
          defenderWon,
        }); // Debug log

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

        console.log("Validation passed, submitting form"); // Debug log
        console.log("Form data:", {
          match_id: matchIdInput.value,
          winner_id: winnerIdInput.value,
          challenger_score: challengerSetsInput.value,
          defender_score: defenderSetsInput.value,
        }); // Debug log

        // Submit the form first
        finishMatchForm.submit();

        // Optionally, show spinner after a short delay if you want
        // setTimeout(() => startSpinner("finishMatchModalContent"), 100);
      });
    } else {
      console.log("Finish match button or form not found");
    }
  }
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

// Initialize all functionality when DOM is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  // Set up click handlers for player table rows
  const playerRows = document.querySelectorAll(".player-row");

  playerRows.forEach((row) => {
    row.addEventListener("click", function () {
      const playerId = this.getAttribute("data-player-id");
      toggleExpandRow(playerId);
    });

    // Apply cursor pointer styling to indicate clickable rows
    row.style.cursor = "pointer";
  });

  // Handle challenge modal show event to update modal content
  const challengeModal = document.getElementById("challengeWindow");
  if (challengeModal) {
    challengeModal.addEventListener("show.bs.modal", function (event) {
      // Extract data from triggering button
      const button = event.relatedTarget;
      const playerId = button.getAttribute("data-player-id");
      const playerName = button.getAttribute("data-player-name");

      // Update modal label with player information
      const modalInputLabel = document.getElementById(
        "challengeWIndowInputLabel"
      );
      if (modalInputLabel) {
        modalInputLabel.textContent = `${playerName} challenges the following:`;
      }

      // Store player ID for form processing
      this.setAttribute("data-current-player-id", playerId);
    });
  }

  // Initialize trainer page specific functionality
  initializeChallengeSystem();
  initializeFinishMatchModal();
});

// Secondary DOM ready handler for challenge modal label updates
document.addEventListener("DOMContentLoaded", function () {
  const challengeModal = document.getElementById("challengeWindow");
  const challengeLabel = document.getElementById("challengeWindowInputLabel");

  challengeModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget; // Button that triggered the modal
    const playerName = button.getAttribute("data-player-name");

    // Update the label text with challenger name
    challengeLabel.textContent = `${playerName} challenges who?`;
  });
});

// Placeholder for jQuery autocomplete functionality
document.addEventListener(
  "DOMContentLoaded",
  () => {
    // $("#input-datalist").autocomplete(); only works with jQuery
  },
  false
);
