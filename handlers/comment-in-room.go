package handlers

import "net/http"

func Comment(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}

	roomID := r.FormValue("roomid")
	comment := r.FormValue("comment")

	room, Exist := rooms[roomID]
	if !Exist {
		http.Error(w, "roomid required", http.StatusNotFound)
		return
	}

	user, Exist := Get_home_user(r)
	if !Exist {
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	com := Comments{
		User: user.Gitea,
		Text: comment,
	}

	room.Comments = append(room.Comments, com)
	SaveRoom()

	http.Redirect(w, r, "/room?id="+roomID, http.StatusSeeOther)

}
