# Use official Node image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files — install dependencies as a cached layer
COPY package*.json ./
RUN npm install

# Copy the rest of the source
COPY . .

# Expose Vite's dev port
EXPOSE 5173

# Always run npm install on start to handle volume overrides,
# then launch Vite dev server accessible outside the container
CMD ["sh", "-c", "npm install && npm run dev -- --host 0.0.0.0"]
