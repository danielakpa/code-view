package handlers

import "net/http"

func ClaimCode(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}

	roomID := r.FormValue("roomid")

	room, exist := rooms[roomID]
	if !exist {

		http.Error(w, "room id not found", http.StatusNotFound)
		return
	}

	if room.CodeLocked {
		http.Error(w, "code is already looked", http.StatusForbidden)
		return
	}

	user, Exist := Get_home_user(r)
	if !Exist {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	room.CodeLocked = true

	room.CodeOwner = user.Gitea
	SaveRoom()

	http.Redirect(w, r, "/room?id="+roomID, http.StatusSeeOther)
}
