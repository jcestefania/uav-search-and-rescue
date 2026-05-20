import tkinter as tk
from tkinter import messagebox

def user_parameters():
    def submit_data():
        data = {
            "pais": entry_pais.get(),
            "municipio": entry_municipio.get(),
            "calle": entry_calle.get(),
            "radio": entry_radio.get(),
            "tipo": entry_tipo.get(),
            "dinamico": entry_dinamico.get(),
            "tam_cuadricula": entry_tam_cuadricula.get(),
        }
        if not all(data.values()):
            messagebox.showwarning("Datos Incompletos", "Por favor, rellena todos los campos.")
            return
        params.update(data)
        root.destroy()

    params = {}

    root = tk.Tk()
    root.title("Parámetros de Entrada")
    root.geometry("400x400")
    root.configure(bg="#f0f4f8")

    title_label = tk.Label(root, text="Parámetros de Inicialización", font=("Arial", 16, "bold"), bg="#f0f4f8", fg="#333")
    title_label.pack(pady=10)

    form_frame = tk.Frame(root, bg="#f0f4f8")
    form_frame.pack(pady=10, padx=20, fill="both", expand=True)

    labels = ["País", "Municipio", "Calle", "Radio", "Tipo", "Dinámico", "Tamaño de Cuadrícula"]
    entries = []

    for i, label_text in enumerate(labels):
        label = tk.Label(form_frame, text=f"{label_text}:", font=("Arial", 12), bg="#f0f4f8", fg="#555")
        label.grid(row=i, column=0, sticky="w", padx=10, pady=5)

        entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        entry.grid(row=i, column=1, padx=10, pady=5)
        entries.append(entry)

    entry_pais, entry_municipio, entry_calle, entry_radio, entry_tipo, entry_dinamico, entry_tam_cuadricula = entries

    submit_button = tk.Button(root, text="Aceptar", command=submit_data, bg="#0078d7", fg="white", font=("Arial", 12, "bold"), relief="flat")
    submit_button.pack(pady=20)

    root.mainloop()
    return params

# Ejemplo de uso
if __name__ == "__main__":
    parameters = user_parameters()
    print(parameters)
