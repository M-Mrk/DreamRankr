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
        modalInputLabel.textContent = `${playerName} fordert den folgenden heraus:`;
      }

      // Store player ID for form submission
      this.setAttribute("data-current-player-id", playerId);
    });
  }
});

function toggleExpandRow(playerId) {
  // Check if we're in mobile or normal view
  const mobileExpandRow = document.getElementById(`expand-mobile-${playerId}`);
  const normalExpandRow = document.getElementById(`expand-normal-${playerId}`);

  // Toggle mobile view expand row
  if (mobileExpandRow) {
    if (
      mobileExpandRow.style.display === "none" ||
      mobileExpandRow.style.display === ""
    ) {
      mobileExpandRow.style.display = "table-row";
    } else {
      mobileExpandRow.style.display = "none";
    }
  }

  // Toggle normal view expand row
  if (normalExpandRow) {
    if (
      normalExpandRow.style.display === "none" ||
      normalExpandRow.style.display === ""
    ) {
      normalExpandRow.style.display = "table-row";
    } else {
      normalExpandRow.style.display = "none";
    }
  }
}

document.addEventListener(
  "DOMContentLoaded",
  (e) => {
    $("#input-datalist").autocomplete();
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
    challengeLabel.textContent = `${playerName} fordert wen heraus?`;
  });
});

// Challenge functionality for trainer page
function initializeChallengeSystem() {
  const challengeModal = document.getElementById("challengeWindow");
  const challengeInput = document.getElementById("input-datalist");
  const challengeDatalist = document.getElementById("list-timezone");
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
      challengeLabel.textContent = playerName + " fordert wen heraus?";

      // Clear previous options and input
      challengeDatalist.innerHTML = "";
      challengeInput.value = "";
      challengeInput.disabled = false;
      challengeInput.placeholder = "Wähle einen Spieler...";

      // Check if player is already rank 1 (highest ranking)
      if (currentPlayer.ranking === 1) {
        challengeInput.placeholder = "Ist bereits der beste";
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
        challengeDatalist.appendChild(option);
      });

      // Store current challenger info for later use
      challengeModal.setAttribute("data-challenger-id", playerId);
      challengeModal.setAttribute("data-challenger-name", playerName);
    });
  });

  // Validate input to only allow eligible players
  challengeInput.addEventListener("input", function () {
    if (this.disabled) return;

    const currentValue = this.value;
    const options = Array.from(challengeDatalist.options).map(
      (option) => option.value
    );

    if (currentValue && !options.includes(currentValue)) {
      this.setCustomValidity("Please select a valid player from the list");
    } else {
      this.setCustomValidity("");
    }
  });

  // Handle form submission
  const startButton = challengeModal.querySelector(".btn-primary");
  if (startButton) {
    startButton.addEventListener("click", function () {
      // Check if input is disabled (rank 1 player)
      if (challengeInput.disabled) {
        alert(
          "Dieser Spieler ist bereits der beste und kann niemanden herausfordern!"
        );
        return;
      }

      const challengedPlayer = challengeInput.value;
      const challengerId = challengeModal.getAttribute("data-challenger-id");
      const challengerName = challengeModal.getAttribute(
        "data-challenger-name"
      );

      if (!challengedPlayer || !challengerId) {
        alert("Please select a player to challenge");
        return;
      }

      // Find challenged player ID
      const challengedPlayerObj = allPlayers.find(
        (p) => p.name === challengedPlayer
      );
      if (!challengedPlayerObj) {
        alert("Invalid player selection");
        return;
      }

      console.log("Challenge:", {
        challenger: { id: challengerId, name: challengerName },
        challenged: { id: challengedPlayerObj.id, name: challengedPlayer },
      });

      // Close modal
      const modalInstance = bootstrap.Modal.getInstance(challengeModal);
      modalInstance.hide();

      // You can add an AJAX call here to submit the challenge
      // fetch('/create_challenge', {
      //     method: 'POST',
      //     headers: {'Content-Type': 'application/json'},
      //     body: JSON.stringify({
      //         challenger_id: challengerId,
      //         challenged_id: challengedPlayerObj.id
      //     })
      // });
    });
  }
}

// Initialize challenge system when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // ...existing code...
  initializeChallengeSystem();
});
