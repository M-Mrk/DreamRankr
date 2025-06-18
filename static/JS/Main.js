function openModal(modalId) {
  modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "block";
  }
}

function closeModal(modalId) {
  modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
  }
}

function openChallengeWindow(playerId) {
  openModal("challengeWindow");
}

// Add event listeners when the DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Add click event listeners to all player rows
  const playerRows = document.querySelectorAll(".player-row");

  playerRows.forEach((row) => {
    row.addEventListener("click", function () {
      const playerId = this.getAttribute("data-player-id");
      toggleExpandRow(playerId);
    });

    // Add cursor pointer style to indicate clickable rows
    row.style.cursor = "pointer";
  });

  // Handle modal show event
  const challengeModal = document.getElementById("challengeWindow");
  if (challengeModal) {
    challengeModal.addEventListener("show.bs.modal", function (event) {
      // Get the button that triggered the modal
      const button = event.relatedTarget;
      const playerId = button.getAttribute("data-player-id");
      const playerName = button.getAttribute("data-player-name");

      // Update modal content
      const modalInputLabel = document.getElementById(
        "challengeWIndowInputLabel"
      );
      if (modalInputLabel) {
        modalInputLabel.textContent = `${playerName} challenges the following:`;
      }

      // Store player ID for form submission
      this.setAttribute("data-current-player-id", playerId);
    });
  }
});

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

document.addEventListener(
  "DOMContentLoaded",
  () => {
    // $("#input-datalist").autocomplete(); only works with jQuery
  },
  false
);

// Add this JavaScript to handle modal updates
document.addEventListener("DOMContentLoaded", function () {
  const challengeModal = document.getElementById("challengeWindow");
  const challengeLabel = document.getElementById("challengeWindowInputLabel");

  challengeModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget; // Button that triggered the modal
    const playerName = button.getAttribute("data-player-name");

    // Update the label text
    challengeLabel.textContent = `${playerName} challenges who?`;
  });
});

// Challenge functionality for trainer page
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

  // Get players data from the page
  const playerRows = document.querySelectorAll(".player-row");
  const allPlayers = Array.from(playerRows).map((row) => ({
    id: row.getAttribute("data-player-id"),
    name: row.getAttribute("data-player-name"),
    ranking: parseInt(row.getAttribute("data-player-id")), // assuming player-id is ranking
  }));

  // Handle challenge button clicks
  document.querySelectorAll(".challenge-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const playerName = this.getAttribute("data-player-name");
      const playerId = this.getAttribute("data-player-id");

      // Find the player's ranking
      const currentPlayer = allPlayers.find((p) => p.name === playerName);
      if (!currentPlayer) return;

      // Update modal title and label
      challengeLabel.textContent = playerName + " challenges who?";

      // Clear previous options and input
      challengeDatalist.innerHTML = "";
      challengeInput.value = "";
      challengeInput.disabled = false;
      challengeInput.placeholder = "Choose a player...";

      // Set challenger ID in hidden input
      challengerIdInput.value = playerId;

      // Check if player is already rank 1 (highest ranking)
      if (currentPlayer.ranking === 1) {
        challengeInput.placeholder = "Is already the best!";
        challengeInput.disabled = true;
        challengeModal.setAttribute("data-challenger-id", "");
        challengeModal.setAttribute("data-challenger-name", "");
        return;
      }

      // Add only players with higher ranking (lower ranking number)
      const eligiblePlayers = allPlayers.filter(
        (p) => p.ranking < currentPlayer.ranking
      );

      eligiblePlayers.forEach((player) => {
        const option = document.createElement("option");
        option.value = player.name;
        option.setAttribute("data-player-id", player.id);
        challengeDatalist.appendChild(option);
      });

      // Store current challenger info for later use
      challengeModal.setAttribute("data-challenger-id", playerId);
      challengeModal.setAttribute("data-challenger-name", playerName);
    });
  });

  // Validate input and update defender ID
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
        // Find the defender's ID
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

  // Handle form submission - make Starten button submit the form
  const startButton = challengeModal.querySelector(".btn-primary");
  const challengeForm = challengeModal.querySelector("form");

  if (startButton && challengeForm) {
    startButton.addEventListener("click", function (e) {
      e.preventDefault(); // Prevent default button behavior

      // Check if input is disabled (rank 1 player)
      if (challengeInput.disabled) {
        alert(
          "This player is already the best and cannot be challenged!"
        );
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

      // Submit the form
      challengeForm.submit();
    });
  }
}

document.addEventListener("DOMContentLoaded", function () {
  initializeChallengeSystem();
});

function startSpinner(id) {
  const modal = document.getElementById(id);
  modal.textContent = "";
  modal.innerHTML =
    '<div class="d-flex justify-content-center"> <div class="spinner-border" role="status"> <span class="visually-hidden">Loading...</span> </div> </div>';
}
