// Fonctions partagées par toutes les pages : appels à l'API, session, cadre commun, états d'affichage.
// Le client ne parle QU'À l'API (jamais à la base de données).
// Le jeton reçu à la connexion est gardé dans sessionStorage : il disparaît à la fermeture de l'onglet.

const PAGE_DU_ROLE = {
  etudiant: "etudiant.html",
  enseignant: "enseignant.html",
  superviseur: "superviseur.html"
};

const LIBELLE_ROLE = {
  etudiant: "Étudiant",
  enseignant: "Enseignant",
  superviseur: "Superviseur"
};

// ---------- Appels à l'API ----------

class ErreurApi extends Error {
  constructor(statut, code, message) {
    super(message);
    this.statut = statut;   // code HTTP (0 si l'API est injoignable)
    this.code = code;
  }
}

// Envoie une requête à l'API et renvoie la réponse JSON.
// En cas d'erreur, lève une ErreurApi avec le code HTTP et le message de l'API.
async function appeler(chemin, methode, corps) {
  const entetes = {};
  const jeton = sessionStorage.getItem("jeton");
  if (jeton) {
    entetes["Authorization"] = "Bearer " + jeton;   // l'API déduit l'identité de ce jeton
  }
  const options = { method: methode || "GET", headers: entetes };
  if (corps !== undefined) {
    entetes["Content-Type"] = "application/json";
    options.body = JSON.stringify(corps);
  }

  let reponse;
  try {
    reponse = await fetch(CONFIG.API_URL + chemin, options);
  } catch (e) {
    throw new ErreurApi(0, "injoignable", "Impossible de joindre le serveur. Vérifiez que l'API est démarrée.");
  }

  let donnees = null;
  try {
    donnees = await reponse.json();
  } catch (e) {
    donnees = null;
  }

  if (!reponse.ok) {
    const message = (donnees && donnees.message) || "Erreur inattendue.";
    const erreur = new ErreurApi(reponse.status, donnees && donnees.erreur, message);
    if (reponse.status === 401 && jeton) {
      deconnecter(message);   // jeton expiré ou refusé : retour à la connexion
    }
    throw erreur;
  }
  return donnees;
}

// ---------- Session ----------

function ouvrirSession(reponseConnexion) {
  sessionStorage.setItem("jeton", reponseConnexion.jeton);
  sessionStorage.setItem("role", reponseConnexion.role);
  sessionStorage.setItem("nom_complet", reponseConnexion.nom_complet);
}

function deconnecter(message) {
  sessionStorage.clear();
  if (message) {
    sessionStorage.setItem("message_connexion", message);
  }
  location.href = "index.html";
}

// À appeler au début de chaque page protégée. Renvoie true si l'utilisateur a le bon rôle.
function exigerRole(role) {
  if (!sessionStorage.getItem("jeton")) {
    deconnecter();
    return false;
  }
  const actuel = sessionStorage.getItem("role");
  if (actuel !== role) {
    location.href = PAGE_DU_ROLE[actuel] || "index.html";
    return false;
  }
  return true;
}

// ---------- Affichage ----------

// Protège l'affichage : tout texte venant de l'API passe par cette fonction avant d'entrer dans la page.
function echapper(texte) {
  const remplacements = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(texte).replace(/[&<>"']/g, function (c) { return remplacements[c]; });
}

// Construit le menu sombre à gauche et renvoie la zone où afficher le contenu de la page.
function monterCadre(sousTitre, libelleMenu) {
  const nom = sessionStorage.getItem("nom_complet") || "";
  const role = sessionStorage.getItem("role");
  document.getElementById("racine").innerHTML =
    '<div class="app"><aside>' +
      '<div class="marque"><span class="logo">É</span><div><strong>Écoléo</strong><small>' + echapper(sousTitre) + '</small></div></div>' +
      '<nav><a class="actif" href="' + PAGE_DU_ROLE[role] + '">' + echapper(libelleMenu) + '</a></nav>' +
      '<div class="profil"><div class="avatar">' + echapper(nom.charAt(0).toUpperCase()) + '</div>' +
      '<div><strong>' + echapper(nom) + '</strong><small>' + echapper(LIBELLE_ROLE[role] || "") + '</small></div></div>' +
      '<button class="lien-deconnexion" id="btn-deconnexion" type="button">Déconnexion</button>' +
    '</aside><main id="contenu"></main></div>';
  document.getElementById("btn-deconnexion").addEventListener("click", function () { deconnecter(); });
  return document.getElementById("contenu");
}

// Les trois états d'une liste : attente, erreur, vide.
function htmlAttente() {
  return '<div class="attente"><span class="spinner"></span>Chargement…</div>';
}

function htmlErreur(erreur) {
  const prefixe = erreur.statut ? erreur.statut + " : " : "";
  return '<div class="bandeau bandeau-erreur" role="alert">' + echapper(prefixe + erreur.message) + '</div>';
}

function htmlVide(message) {
  return '<div class="vide">' + echapper(message) + '</div>';
}

// Formats d'affichage : la date arrive de l'API en AAAA-MM-JJ.
function formaterDate(iso) {
  const p = iso.split("-");
  return p[2] + "/" + p[1] + "/" + p[0];
}

function formaterNote(valeur) {
  return valeur.toFixed(1) + "/20";
}

function classeNote(valeur) {
  return valeur >= 16 ? "note note-haute" : "note";
}
