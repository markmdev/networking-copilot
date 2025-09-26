# Build stage
FROM node:20-alpine AS builder
WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./

# Ensure production build picks up runtime API URL if provided
ARG NEXT_PUBLIC_API_BASE_URL=http://backend:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

RUN npm run build

# Runtime stage
FROM node:20-alpine
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app .

EXPOSE 3000

CMD ["npm", "run", "start"]
