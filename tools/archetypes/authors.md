---
id: "{{ .Name }}"
name: "{{ replace .Name "-" " " | title }}"
title: "{{ replace .Name "-" " " | title }}"
type: staff
role: ""
company: ""
github: ""
linkedin: ""
image: avatar.jpg
---

Short bio. Posts refer to `id`, not the display name. The id is the public address, /author/<id>/. Use name-surname: lowercase letters, digits, and hyphens. Not name_surname or name.surname.
