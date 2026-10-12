// Llamadas al backend

const TOKEN_KEY = "token"

export function guardarToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function leerToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function borrarToken() {
  localStorage.removeItem(TOKEN_KEY)
}

async function pedir(ruta, opciones = {}) {
  const token = leerToken()
  const respuesta = await fetch(`/api${ruta}`, {
    ...opciones,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...opciones.headers,
    },
  })

  if (respuesta.status === 401) {
    borrarToken()
    window.location.href = "/login"
    throw new Error("Sesion expirada")
  }

  if (!respuesta.ok) {
    const error = await respuesta.json().catch(() => ({}))
    throw new Error(error.detail || "Ocurrio un error inesperado")
  }

  return respuesta.status === 204 ? null : respuesta.json()
}

export const api = {
  get: (ruta) => pedir(ruta),
  post: (ruta, datos) => pedir(ruta, { method: "POST", body: JSON.stringify(datos) }),
  put: (ruta, datos) => pedir(ruta, { method: "PUT", body: JSON.stringify(datos) }),
  del: (ruta) => pedir(ruta, { method: "DELETE" }),
}

export async function iniciarSesion(email, password) {
  const cuerpo = new URLSearchParams({ username: email, password })
  const respuesta = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: cuerpo,
  })

  if (!respuesta.ok) {
    const error = await respuesta.json().catch(() => ({}))
    throw new Error(error.detail || "No fue posible iniciar sesion")
  }

  const datos = await respuesta.json()
  guardarToken(datos.access_token)
  return datos
}

export async function descargarReporte(formato) {
  const respuesta = await fetch(`/api/reportes/exportar/${formato}`, {
    headers: { Authorization: `Bearer ${leerToken()}` },
  })
  if (!respuesta.ok) throw new Error("No se pudo exportar el reporte")

  const blob = await respuesta.blob()
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement("a")
  enlace.href = url
  enlace.download = `historial_labores.${formato === "excel" ? "xlsx" : "csv"}`
  enlace.click()
  URL.revokeObjectURL(url)
}
