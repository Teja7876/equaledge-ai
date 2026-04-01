#!/bin/bash

jq -r '
map({
id: .id,
title: .title.rendered,
slug: .slug,
content: (.content.rendered
| gsub("<[^>]*>";"")
| gsub("&nbsp;";" ")
| gsub("&amp;";"&"))
})
' posts_all.json > posts_clean.json
