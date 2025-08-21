# Use an official Node.js runtime as a parent image
FROM node:20-alpine as build

# Set the working directory in the container
WORKDIR /app

# Define build argument
ARG VITE_API_URL

# Create a .env file in the container
RUN echo "VITE_API_URL=${VITE_API_URL}" > .env

# Copy the entire frontend application source code
COPY . .

# Install dependencies
RUN npm install

# Build the app for production
RUN npm run build

# Production stage
FROM nginx:stable-alpine as production

# Copy the built assets from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy the nginx config file
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 to the outside world
EXPOSE 80

# Command to run nginx
CMD ["nginx", "-g", "daemon off;"] 