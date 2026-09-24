document.addEventListener("DOMContentLoaded", function () {
  const carte = document.getElementById("feedback-carte");
  if (!carte) return;

  const fonctionnalite = carte.dataset.fonctionnalite;

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }

  function afficher(html) {
    if (!html) return;
    carte.innerHTML = html;
    carte.style.display = "block";
    attacherEcouteurs();
  }

  function envoyerReponse(questionId, reponse, commentaire) {
    const corps = new URLSearchParams({ reponse: reponse || "", commentaire: commentaire || "" });
    fetch(`/feedback/repondre/${questionId}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: corps,
    })
      .then((r) => r.json())
      .then((data) => afficher(data.html))
      .catch(() => {
        carte.style.display = "none";
      });
  }

  function attacherEcouteurs() {
    const widget = carte.querySelector(".feedback-widget");
    if (!widget) return;
    const questionId = widget.dataset.questionId;

    carte.querySelectorAll(".feedback-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        envoyerReponse(questionId, btn.dataset.reponse, "");
      });
    });

    const formTexte = carte.querySelector(".feedback-form-texte");
    if (formTexte) {
      formTexte.addEventListener("submit", function (e) {
        e.preventDefault();
        const commentaire = formTexte.querySelector("textarea[name=commentaire]").value;
        envoyerReponse(questionId, "", commentaire);
      });
    }
  }

  fetch(`/feedback/question/${fonctionnalite}/`)
    .then((r) => r.json())
    .then((data) => afficher(data.html))
    .catch(() => {});
});