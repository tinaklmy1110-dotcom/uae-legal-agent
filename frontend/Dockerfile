FROM node:20-alpine

WORKDIR /app

COPY package.json package.json
COPY package-lock.json package-lock.json
COPY tsconfig.json tsconfig.json
COPY next-env.d.ts next-env.d.ts
COPY tailwind.config.ts tailwind.config.ts
COPY postcss.config.js postcss.config.js
COPY next.config.js next.config.js
COPY app app
COPY components components
COPY lib lib

RUN npm install

ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3000

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
