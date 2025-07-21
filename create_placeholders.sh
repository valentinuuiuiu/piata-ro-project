#!/bin/bash

# Create placeholder images for all the missing files
for i in {54..61}; do
  for j in {0..9}; do
    mkdir -p "/home/shiva/Desktop/piata-ro-project/media/listings/$((i % 9 + 1))/$i"
    cat > "/home/shiva/Desktop/piata-ro-project/media/listings/$((i % 9 + 1))/$i/listing_${i}_${j}.jpg" << EOF
<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="300" height="200" fill="#f0f0f0"/>
  <text x="150" y="100" font-family="Arial" font-size="20" text-anchor="middle" fill="#999">Image ${i}_${j}</text>
</svg>
EOF
  done
done